// Pure checks for the tool-call guard: no `$`, so tests can call them directly.
// Deliberately narrow: catastrophic deletes, force-pushes to main, secrets files.

const DANGEROUS_RM_TARGETS = new Set([
  '/', '/*', '~', '~/', '~/*', '$HOME', '$HOME/', '${HOME}', '.', './', '..', '../', '*', '.*', '.git',
])
const SECRET_FILE = /(^|\/)\.env(\.[\w-]+)?$/
const SECRET_OK = /\.(example|sample|template|dist)$/
const READERS = new Set(['cat', 'less', 'more', 'head', 'tail', 'bat', 'batcat', 'cp', 'scp', 'base64', 'xxd', 'strings', 'source', '.'])

/** Shell-ish word splitting: honours single and double quotes and backslashes. */
function words(part: string): string[] {
  const out: string[] = []
  let cur = ''
  let quote: string | null = null
  let has = false
  for (let i = 0; i < part.length; i++) {
    const c = part[i] ?? ''
    if (quote) {
      if (c === quote) quote = null
      else if (c === '\\' && quote === '"' && i + 1 < part.length) cur += part[++i]
      else cur += c
    } else if (c === "'" || c === '"') {
      quote = c
      has = true
    } else if (c === '\\' && i + 1 < part.length) {
      cur += part[++i]
      has = true
    } else if (/\s/.test(c)) {
      if (cur || has) out.push(cur)
      cur = ''
      has = false
    } else {
      cur += c
      has = true
    }
  }
  if (cur || has) out.push(cur)
  return out
}

/** One word list per simple command; heredoc bodies and quoted separators don't split. */
export function segments(cmd: string): string[][] {
  const noHeredocs = cmd.replace(/<<-?\s*['"]?(\w+)['"]?[^\n]*\n[\s\S]*?^\s*\1\s*$/gm, '')
  const parts: string[] = []
  let cur = ''
  let quote: string | null = null
  for (let i = 0; i < noHeredocs.length; i++) {
    const c = noHeredocs[i] ?? ''
    if (quote) {
      if (c === quote) quote = null
      cur += c
      continue
    }
    if (c === "'" || c === '"') {
      quote = c
      cur += c
      continue
    }
    const two = noHeredocs.slice(i, i + 2)
    if (two === '&&' || two === '||') {
      parts.push(cur)
      cur = ''
      i++
    } else if (c === ';' || c === '|' || c === '\n') {
      parts.push(cur)
      cur = ''
    } else {
      cur += c
    }
  }
  parts.push(cur)
  return parts.map(words).filter(w => w.length > 0)
}

function rmProblem(cmd: string): string | undefined {
  for (const w of segments(cmd)) {
    const at = w.indexOf('rm')
    if (at < 0) continue
    const args = w.slice(at + 1)
    const flags = args.filter(a => a.startsWith('-') && !a.startsWith('--')).map(a => a.slice(1)).join('')
    const isRecursive = /r/i.test(flags) || args.includes('--recursive')
    const bad = args.filter(a => !a.startsWith('-') && DANGEROUS_RM_TARGETS.has(a))
    if (isRecursive && bad.length > 0) return `recursive rm on ${bad.join(', ')}`
  }
  return undefined
}

function pushProblem(cmd: string): string | undefined {
  for (const w of segments(cmd)) {
    if (w[0] !== 'git' || w[1] !== 'push') continue
    const isForce = w.some(a => a === '--force' || a === '-f')
    const toMain = w.slice(2).some(a => ['main', 'master'].includes(a.split(':').pop() ?? ''))
    if (isForce && toMain) return 'force push to main/master'
  }
  return undefined
}

function isSecret(path: string): boolean {
  return SECRET_FILE.test(path) && !SECRET_OK.test(path)
}

/** Why a tool call should be refused, or undefined to let it through. */
export function problem(tool: string, input: Record<string, unknown>): string | undefined {
  if (['Read', 'Edit', 'Write', 'MultiEdit', 'NotebookEdit'].includes(tool)) {
    const path = String(input.file_path ?? input.notebook_path ?? '')
    return isSecret(path) ? `access to secrets file ${path}` : undefined
  }
  if (tool !== 'Bash') return undefined
  const cmd = String(input.command ?? '')
  for (const w of segments(cmd)) {
    const name = (w[0] ?? '').split('/').pop() ?? ''
    if (!READERS.has(name)) continue
    const hit = w.slice(1).find(a => !a.startsWith('-') && isSecret(a))
    if (hit) return `access to secrets file ${hit}`
  }
  return rmProblem(cmd) ?? pushProblem(cmd)
}
