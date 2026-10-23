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

The portable Markdown file is non-executable. It embeds policy, contracts, and fictional examples, but an assistant still needs separate, explicitly authorized tools to read private files or act on external services.

Compatibility means the host can load and follow the skill. It does not mean the repository installs an application runtime or grants the host new account access.

## Capability boundaries

- No OpenAI API key is required for local validation or packaging.
- No email, LinkedIn, browser, portal, or job-board connector is bundled.
- Host tools and permissions determine whether discovery or submission is possible.
- A missing connector results in a manual handoff, not a submission claim.
- Provider rules, authentication challenges, and first-party confirmation requirements still apply.

## Updating versions

Keep `packaging/metadata.json`, `packaging/portable/plugin.json`, and `packaging/codex-plugin-template/job-application-manager/.codex-plugin/plugin.json` on the same semantic version. Run the release validation after every metadata or canonical-skill change.
