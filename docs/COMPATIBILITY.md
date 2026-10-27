# Compatibility

## Canonical source

`.agents/skills/manage-job-applications/` is the maintained source. Make policy, schema, fixture, or validator changes there first, then rebuild other formats.

## Supported package forms

| Form | Output | Intended use |
| --- | --- | --- |
| Repository skill | `.agents/skills/manage-job-applications/` | Agents that discover repository skills. |
| Portable Markdown | `dist/portable/manage-job-applications.md` | Assistants that accept a single instruction or knowledge file. |
| Agent Plugin | `dist/portable-plugin/job-application-manager/` | Hosts implementing Agent Plugins 1.0 root `plugin.json` discovery. |
| Codex compatibility plugin | `dist/codex-plugin/job-application-manager/` | Codex installations using `.codex-plugin/plugin.json`. |

The portable Markdown file is non-executable. It embeds policy, contracts, fictional examples, and internal source navigation, but not executable Python helpers. Use a repository or plugin package when local validation is required. An assistant still needs separate, explicitly authorized tools to read private files or act on external services.

Compatibility means the host can load and follow the skill. Multi-agent behavior is capability-gated: hosts with subagents may use bounded delegation, while other hosts execute the same roles sequentially. It does not mean the repository installs an application runtime or grants the host new account access.

For contributors using a source checkout in current Codex releases, `.codex/agents/` defines five project-scoped job-workflow specialists and `.codex/config.toml` enables up to five concurrent spawned threads besides the main thread. Those repository development defaults are intentionally not bundled in the Codex compatibility plugin; the plugin contains the canonical skill and role references instead. The formal architecture ceiling remains nineteen specialists plus the main orchestrator, but the lower host/configuration limit always wins. Custom-agent instructions inherit the parent session's tools and permissions; they do not create per-agent filesystem or network isolation.

## Capability boundaries

- No OpenAI API key is required for local validation or packaging.
- No email, LinkedIn, browser, portal, or job-board connector is bundled.
- Host tools and permissions determine whether discovery, delegation, or submission is possible.
- Subagent tools are supplied by the host and are never declared or emulated by this package.
- The main agent remains the only approval holder, external actor, and canonical checkpoint writer.
- A missing connector results in a manual handoff, not a submission claim.
- Provider rules, authentication challenges, and first-party confirmation requirements still apply.

## Updating versions

Keep `packaging/metadata.json`, `packaging/portable/plugin.json`, and `packaging/codex-plugin-template/job-application-manager/.codex-plugin/plugin.json` on the same semantic version. Run the release validation after every metadata or canonical-skill change.
