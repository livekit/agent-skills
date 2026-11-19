# Publishing to plugin directories

This repo is listed in two directories. Claude updates itself from `main`. ChatGPT and Codex need a new upload for each release.

Before you start, check that `version` matches in `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`. Raise it in both for every release.

## Claude

Who can submit:

- On a Team plan, only an Owner can submit.
- On an Enterprise plan, an Owner can give another member the **Directory** permission through a custom role under **Organization settings > Roles**.

Submit from the LiveKit organization, not a personal account. The first organization to submit a repository holds its listing.

The LiveKit API MCP server is its own listing. Submit it first as an **MCP connector** with the URL `https://api.livekit.cloud/mcp`, then submit this plugin and pair the two listings. Both must come from the same organization. The plugin points at the same URL, so people with both see one set of tools.

1. Open [claude.ai/directory/manage](https://claude.ai/directory/manage) and start a plugin submission. Connect a GitHub account that has push access to this repo.
2. **Source:**
   - Repository: `livekit/agent-skills`
   - Plugin path: leave it blank.
   - Branch: `main`.

   Select **Validate**. The listing name, description, icon, and links come from `.claude-plugin/plugin.json` and the README. To change them, edit the repo and validate again.
3. **Data handling:**
   - Reads personal data: yes. On the user's request, the plugin reads session data from the user's own LiveKit Cloud projects, such as transcripts and logs, through the LiveKit API MCP server or the LiveKit CLI. That data can contain personal information about the people who talked to their agent.
   - Stores personal data: no.
   - Sends data to services other than its declared connectors: no. The declared connectors are the LiveKit API MCP server (`https://api.livekit.cloud/mcp`) and the LiveKit Docs MCP server. The CLI talks only to the user's own LiveKit Cloud project.
   - Authentication: OAuth 2.1. The user signs in to LiveKit and approves the app. Workspace admins can turn MCP off or allow only some apps.
   - Retention: none. The plugin stores nothing.
   - Intended for people under 18: no.
4. **Compliance:**
   - Contact email: `support@livekit.io`, a team inbox rather than a personal address. Anthropic sends review updates there, so tell whoever triages it to forward them.
   - Read and select the four acknowledgements.
5. **Review and submit:**
   - How new versions reach the directory: **GitHub push webhook**.
   - Turn on **Auto-publish passing versions**.
   - Select **Submit for review**.

The icon becomes the listing icon the first time the plugin is saved or submitted, and can't change after that. To check locally first, run `claude plugin validate .`.

## ChatGPT and Codex

Who can submit:

- An organization Owner on the OpenAI platform, or a member an Owner grants **Apps Management Write** through organization roles.
- The organization must finish business verification in organization settings first, so the listing shows LiveKit as the developer.

The plugin holds the skills and one MCP server, the LiveKit API at `https://api.livekit.cloud/mcp`. OpenAI allows one MCP server per plugin, so the Docs MCP server is Claude-only; the skills reach current docs through `lk docs`. An MCP server can't be added to a plugin that was first submitted as skills-only, so the first upload must include it.

Before you start:

- The MCP server is live in production.
- Domain verification: OpenAI gives a token in the portal. Serve it as plain text at `https://api.livekit.cloud/.well-known/openai-apps-challenge`.
- Reviewer access: OpenAI's review inbox (`mcp-review@theaicompany.org`, the address the portal fills in) must already be a member of a demo project with sample sessions, a builder agent, and simulation runs, so the reviewer has nothing to set up. Under **Review details**, choose the magic link or email code sign-in.
- The five positive and three negative test cases are in `.codex-plugin/plugin.json` under `extensions.com.openai.review`, with the release notes under `publication`. Run each case against the reviewer account first.
- Purchases: OpenAI's plugin guidelines (section 5.1) don't let a plugin sell digital services or start a checkout. The plugin sells nothing: the MCP server mirrors the LiveKit API, and anything it does bills the user's existing LiveKit account like any other usage. Keep buying and pricing out of the listing copy, test cases, and demo video. If review flags a tool such as `purchase_phone_number`, hide it from ChatGPT.
- A demo video that walks through the test cases. Add its URL to the same `review` object as `demo_recording_url` before you build the ZIP.

1. Build the package with `./scripts/build-openai-zip.sh`. It writes `dist/livekit-openai-<version>.zip` with the MCP config at `.mcp.json`.
2. Open [platform.openai.com/plugins](https://platform.openai.com/plugins), select the LiveKit organization and project, then select **Upload new or existing plugin** and **Upload plugin**. Don't choose **Skills only**.
3. Check the listing the portal shows, which comes from `.codex-plugin/plugin.json`:
   - Name: LiveKit.
   - Short description: "Build and ship voice agents."
   - Category: Developer Tools.
   - Icon: `assets/icon.png`.

   If the portal offers different category names, pick the closest developer category.
4. Check the MCP server's authentication. It's OAuth with a Client ID Metadata Document (`.codex-plugin/mcp.json`), so the portal needs no client ID or secret.
5. The test cases, demo video URL, and release notes import from the ZIP and are read-only in the portal; to change them, edit the manifest and upload again. Under **Review details**, enter the reviewer account's sign-in. Credentials go in the portal, never in the ZIP.
6. Wait for the skill and tool scans to pass, select **Submit for review**, and answer the policy attestations. OpenAI sends review feedback by email.
7. After approval, open the approved version and select **Publish plugin**.

Changes to the MCP server's tools reach users without a new upload: OpenAI scans the server daily. Changing the server's URL needs OpenAI support.

To release a skill or listing update, raise the version, rebuild the ZIP, and upload it as a new version of the existing plugin. Each version gets its own review, and only one review can run at a time.
