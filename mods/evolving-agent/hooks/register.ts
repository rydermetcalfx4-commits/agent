import type { Register, EngineInterface } from 'claude-code'
import { problem } from './guard.ts'
import { appendLine, EVOLUTION, FAILURES, LESSONS, USAGE, oneLine, parseLessons, section, status } from './memory.ts'

const readOr = (async ($: EngineInterface, path: string) => {
  try {
    return await $.fs.read(path)
  } catch {
    return ''
  }
})

const append = async ($: EngineInterface, path: string, line: string) =>
  $.fs.write(path, appendLine(await readOr($, path), line))

const today = () => new Date().toISOString().slice(0, 10)

export const register: Register = on => {
  // Seed the project's memory once, register /agent-status.
  on('session.start', async ($, e, next) => {
    if (!(await $.fs.exists(LESSONS))) {
      await $.fs.write(LESSONS, await $.fs.read(`${$.plugin.root}/templates/learnings.md`))
    }
    if (!(await $.fs.exists(EVOLUTION))) {
      await $.fs.write(EVOLUTION, await $.fs.read(`${$.plugin.root}/templates/EVOLUTION.md`))
    }
    await $.command.register({
      name: 'agent-status',
      description: "Shows the evolving agent's generation, lessons, unprocessed failures and skill use.",
    })
    return next(e)
  })

  on('command.run', { command: 'agent-status' }, async $ => ({
    text: status(await readOr($, LESSONS), await readOr($, FAILURES), await readOr($, USAGE), await readOr($, EVOLUTION)),
  }))

  // Inject the rules and every high-confidence lesson into the system prompt.
  on('prompt.compose', async ($, e, next) => {
    const composed = await next(e)
    const text = section(parseLessons(await readOr($, LESSONS)))
    return { sections: [...composed.sections, { id: 'evolving-agent:memory', text, scope: 'session' as const }] }
  })

  // One hook per tool call: the guard judges first (refusing catastrophic deletes, force-pushes to main and
  // secrets files), then the call runs and its outcome is logged for the evolve and curate skills.
  on('tool.call', async ($, e, next) => {
    const input = e as unknown as Record<string, unknown>
    const why = problem(String(e.tool), input)
    if (why) return { deny: `evolving-agent: blocked ${why}. If the user really wants this, ask them to run it themselves.` }
    const ran = await next(e)
    if (e.tool === 'Skill' && ran.deny === undefined) {
      await append($, USAGE, `${today()}\t${String(input.skill ?? '?')}`).catch(() => undefined)
    }
    if (ran.deny === undefined && ran.isError === true) {
      const what = String(input.command ?? input.file_path ?? input.url ?? input.pattern ?? '')
      const line = `${today()} | ${String(e.tool)} | ${oneLine(what, 120)} | ${oneLine(ran.text ?? '', 200)}`
      await append($, FAILURES, line).catch(() => undefined)
    }
    return ran
  }).catch(($, e, next) => (next.called ? next(e) : { deny: 'evolving-agent: its guard failed, so the call was refused.' }))
}
