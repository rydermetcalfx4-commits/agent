import { describe, expect, test } from 'claude-code/testing'
import type { On } from 'claude-code'
import { problem, segments } from '../hooks/guard.ts'
import { parseLessons, section, status } from '../hooks/memory.ts'

/** An in-memory file system beneath the plugin. */
function memoryFs(on: On, seed: Record<string, string> = {}) {
  const files = new Map(Object.entries(seed))
  const find = (path: string) =>
    [...files.keys()].find(k => path === k || path.endsWith(`/${k}`) || k.endsWith(`/${path}`))
  on('fs.read', ($, e) => {
    const key = find(e.path)
    return key === undefined ? { deny: `ENOENT ${e.path}` } : { value: files.get(key) ?? '' }
  })
  on('fs.write', ($, e) => {
    files.set(find(e.path) ?? e.path, e.text)
    return { value: undefined }
  })
  on('fs.exists', ($, e) => ({ value: find(e.path) !== undefined }))
  return { files, get: (path: string) => files.get(find(path) ?? path) }
}

const LESSONS = `# Learnings
- [0.9] 2026-10-14 — Strong lesson.
- [0.5] 2026-10-14 — Weak lesson.
not a lesson
`

describe('guard (pure)', () => {
  const blocked: [string, Record<string, unknown>][] = [
    ['Bash', { command: 'rm -rf /' }],
    ['Bash', { command: 'cd x && rm -fr ~' }],
    ['Bash', { command: 'rm -r -f .' }],
    ['Bash', { command: 'git push --force origin main' }],
    ['Bash', { command: 'git push -f origin HEAD:main' }],
    ['Bash', { command: 'echo hi && head -5 config/.env' }],
    ['Read', { file_path: '/app/.env' }],
  ]
  const allowed: [string, Record<string, unknown>][] = [
    ['Bash', { command: 'rm -rf build/ dist' }],
    ['Bash', { command: 'git push --force-with-lease origin main' }],
    ['Bash', { command: 'git push -u origin feature/x' }],
    ['Bash', { command: 'git commit -m "cat .env is blocked; rm -rf / too"' }],
    ['Bash', { command: "cat >> NOTES.md <<'EOF'\n- guard blocks .env reads\nEOF" }],
    ['Read', { file_path: '/app/.env.example' }],
    ['Read', { file_path: '/app/src/environment.ts' }],
    ['Grep', { pattern: '.env' }],
  ]
  for (const [tool, input] of blocked) {
    test(`blocks ${tool} ${JSON.stringify(input)}`, () => expect(problem(tool, input)).toBeDefined())
  }
  for (const [tool, input] of allowed) {
    test(`allows ${tool} ${JSON.stringify(input)}`, () => expect(problem(tool, input)).toBeUndefined())
  }
  test('quoted separators do not split commands', () => {
    expect(segments('git commit -m "a && b; c" && ls')).toEqual([['git', 'commit', '-m', 'a && b; c'], ['ls']])
  })
})

describe('memory (pure)', () => {
  test('parses only well-formed lessons', () => {
    expect(parseLessons(LESSONS).map(l => l.confidence)).toEqual([0.9, 0.5])
  })
  test('injects lessons at 0.7 and above only', () => {
    const text = section(parseLessons(LESSONS))
    expect(text).toContain('Strong lesson.')
    expect(text).not.toContain('Weak lesson.')
  })
  test('status counts lessons, failures and skill use', () => {
    const text = status(LESSONS, 'a | b\nc | d\n', '2026-10-14\tevolve\n2026-10-14\tevolve\n', '## Generation 3 — x\n')
    expect(text).toContain('generation: 3')
    expect(text).toContain('lessons: 2 (1 injected')
    expect(text).toContain('unprocessed failures: 2')
    expect(text).toContain('evolve ×2')
  })
})

describe('hooks through the engine', () => {
  test('a dangerous Bash call is refused before it runs', async ($, on) => {
    let ran = false
    memoryFs(on)
    on('tool.call', () => {
      ran = true
      return { result: 'ran' }
    })
    const r = await $.tool.call({ tool: 'Bash', command: 'rm -rf ~' })
    expect(ran).toBe(false)
    expect(r.deny ?? r.text ?? '').toContain('blocked')
  })

  test('a failed call is logged to failures.log', async ($, on) => {
    const fs = memoryFs(on)
    on('tool.call', () => ({ result: 'x', text: 'boom\nline two', isError: true }))
    await $.tool.call({ tool: 'Bash', command: 'make\nbuild' })
    const log = fs.get('.evolving-agent/failures.log') ?? ''
    expect(log).toContain('| Bash | make build | boom line two')
  })

  test('skill use is logged', async ($, on) => {
    const fs = memoryFs(on)
    on('tool.call', () => ({ result: 'ok' }))
    await $.tool.call({ tool: 'Skill', skill: 'evolve' })
    expect(fs.get('.evolving-agent/skill-usage.log') ?? '').toContain('\tevolve')
  })

  test('the system prompt gains the rules and strong lessons', async ($, on) => {
    memoryFs(on, { '.evolving-agent/learnings.md': LESSONS })
    on('prompt.compose', () => ({ sections: [{ id: 'intro', text: 'base', scope: 'shared' as const }] }))
    const { sections } = await $.prompt.compose({
      model: 'm', promptModel: 'm', surfaces: [], tools: [], outputStyle: null, traits: [],
    })
    const mine = sections.find(s => s.id === 'evolving-agent:memory')
    expect(mine?.scope).toBe('session')
    expect(mine?.text).toContain('Strong lesson.')
    expect(sections[0]?.id).toBe('intro')
  })

  test('/agent-status reports from the memory files', async ($, on) => {
    memoryFs(on, { '.evolving-agent/learnings.md': LESSONS, '.evolving-agent/failures.log': 'x | y\n' })
    const r = await $.command.run({
      command: 'agent-status', args: '', origin: { kind: 'composer' }, presentation: { isFullscreen: false, columns: 80 },
    })
    expect(r.text).toContain('unprocessed failures: 1')
  })
})
