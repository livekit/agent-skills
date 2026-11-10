# Publishing to plugin directories

This repo is listed in two directories. Claude updates itself from `main`. ChatGPT and Codex need a new upload for each release.

Before you start, check that `version` matches in `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`. Raise it in both for every release.

## Claude

Who can submit:

- On a Team plan, only an Owner can submit.
- On an Enterprise plan, an Owner can give another member the **Directory** permission through a custom role under **Organization settings > Roles**.

Submit from the LiveKit organization, not a personal account. The first organization to submit a repository holds its listing.

1. Open [claude.ai/directory/manage](https://claude.ai/directory/manage) and start a plugin submission. Connect a GitHub account that has push access to this repo.
2. **Source:**
   - Repository: `livekit/agent-skills`
   - Plugin path: leave it blank.
   - Branch: `main`.

   Select **Validate**. The listing name, description, icon, and links come from `.claude-plugin/plugin.json` and the README. To change them, edit the repo and validate again.
3. **Data handling:**
   - Reads personal data: yes. On the user's request, the skills read session data from the user's own LiveKit Cloud project through the LiveKit CLI, such as transcripts and logs. That data can contain personal information about the people who talked to their agent.
   - Stores personal data: no.
   - Sends data to services other than its declared connectors: no. The declared connector is the LiveKit Docs MCP server. The CLI talks only to the user's own LiveKit Cloud project.
   - Retention: none. The plugin stores nothing.
   - Intended for people under 18: no.
4. **Compliance:**
   - Contact email: a LiveKit team alias, not a personal address.
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

This is a skills-only plugin. An MCP server can't be added to a skills-only plugin later. Adding the Docs MCP server would mean a new plugin.

1. Build the package with `./scripts/build-openai-zip.sh`. It writes `dist/livekit-openai-<version>.zip`.
2. Open [platform.openai.com/plugins](https://platform.openai.com/plugins), select the LiveKit organization and project, then select **Upload new or existing plugin** and **Upload plugin**. Choose **Skills only**.
3. Check the listing the portal shows, which comes from `.codex-plugin/plugin.json`:
   - Name: LiveKit.
   - Short description: "Build and ship voice agents."
   - Category: Developer Tools.
   - Icon: `assets/icon.png`.

   If the portal offers different category names, pick the closest developer category.
4. Wait for the skill scans to pass, select **Submit for review**, and answer the policy attestations. OpenAI sends review feedback by email.
5. After approval, open the approved version and select **Publish plugin**.

To release an update, raise the version, rebuild the ZIP, and upload it as a new version of the existing plugin. Each version gets its own review, and only one review can run at a time.
