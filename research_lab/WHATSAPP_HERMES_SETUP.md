# Check Puppy50 progress from WhatsApp through Hermes

**Status of this repository:** The read-only Puppy50 status skill and an
independent GitHub Actions smoke test are implemented. **WhatsApp is NOT
connected or QR-paired** to the owner's phone. No hosted Hermes gateway,
Qwen3.8 GPU server, new phone number, or paid cloud server was provisioned.

## Why messages will not stop the research

Puppy50 builds and the guarded QEMU verification runs execute as separate
GitHub Actions jobs. Sending WhatsApp or ChatGPT messages cannot stop those
jobs by itself. Avoid authorizing any bot commands that alter GitHub
workflow state; the `puppy50-progress` skill is intentionally **GET-only**.

## Choose a machine for Hermes

Run Hermes Gateway on an **always-on machine** (an owned Linux computer or
an explicitly approved VPS), with a configured and available LLM provider.
Do **not** put WhatsApp session credentials on an ephemeral GitHub Actions
runner or publish their files to GitHub. If the machine shuts down,
messages will not receive agent replies until it restarts. The original
GitHub Actions research workflows may continue independently.

Hermes needs a responding model to understand your questions. The
previously tested Qwen3.5-0.8B CPU CI model is too small to rely on for
engineering and not available after that CI job ends. Prefer a secured
external inference provider or an operator-hosted Qwen3.8 GPU backend.

## Install the read-only progress skill

On the Hermes gateway machine (with git and Python 3 installed):

```bash
git clone --depth 1 https://github.com/74127418528426leo-del/Test.git puppy50-status-clone
mkdir -p "$HOME/.hermes/skills/engineering"
cp -R puppy50-status-clone/research_lab/hermes_skills/puppy50-progress \
  "$HOME/.hermes/skills/engineering/"
# Run without any token before enabling WhatsApp:
python3 "$HOME/.hermes/skills/engineering/puppy50-progress/scripts/status.py" progress
python3 "$HOME/.hermes/skills/engineering/puppy50-progress/scripts/status.py" fastest
hermes skills list
```

The skill performs **read-only public GitHub API calls**. Its bundled
script never invokes a shell, modifies repository state, or calls GitHub
Actions dispatch. For stronger isolation, run the Hermes gateway itself
in an isolated, unprivileged container with no GitHub write token and
no production files mounted. Hermes terminal permissions are more
powerful than this status script, so don't give the WhatsApp gateway
write permissions or privileged host access.

## Pair WhatsApp yourself

Official Hermes instructions:
https://hermes-agent.nousresearch.com/docs/user-guide/messaging/whatsapp

1. On your own machine, install an up-to-date Hermes Agent and
   Node.js 20+ per the official installer, and **verify its model provider
   answers** before messaging.
2. Run `hermes whatsapp`. Choose **self-chat** to message yourself
   from your own account, or **bot** for a dedicated second number.
3. On your iPhone open WhatsApp → Settings → **Linked Devices** →
   **Link a Device** and scan Hermes's QR code.
4. Restrict access in the Hermes private `~/.hermes/.env`:
   `WHATSAPP_ENABLED=true`,
   `WHATSAPP_MODE=self-chat` (or `bot`),
   `WHATSAPP_ALLOWED_USERS=YOUR_COUNTRY_CODE_AND_NUMBER`
   (digits only; never publish your number).
5. For unauthorized direct messages choose
   `whatsapp.unauthorized_dm_behavior: ignore` in your Hermes config.
6. Start the gateway with `hermes gateway` to test interactively.
   Install it as an OS service with `hermes gateway install` only after
   confirming your account, provider and model work.
7. Message **yourself** in WhatsApp (self-chat mode) or send a message
   to the bot's dedicated number. Ask:
   `/puppy50-progress progress`
   or `/puppy50-progress latest` or `/puppy50-progress fastest`.

No QR can be scanned or personal WhatsApp session established by
ChatGPT in this conversation. Never paste the WhatsApp session data or
private tokens into chat or commit them to the repository.

### Risk: built-in WhatsApp bridge

Hermes's built-in Baileys bridge uses WhatsApp Web, not Meta's official
Business Cloud API. WhatsApp can restrict accounts using unofficial
automations. A dedicated bot number reduces the impact on your personal
account. If you need a more stable officially supported channel,
use Hermes's **WhatsApp Business Cloud API integration** with a Meta
Business account and properly configured webhook instead.

## Example status messages

- **Puppy50 progress** → verified VM goal status, number of recorded
  experiments, queued candidates and latest run URL.
- **Puppy50 latest** → last recorded BIOS/UEFI cold Firefox frames, reason.
- **Puppy50 fastest** → *slowest of the four boots* on the best complete
  four-boot trial. This avoids reporting a cherry-picked fast BIOS boot.
- **Puppy50 failures** → last failed experiment and evidence URL.

Green AI-research CI does **not** mean the OS reached five seconds.
The report requires a complete independently verified BIOS+UEFI
candidate and a separate physical Acer test before hardware claims.
