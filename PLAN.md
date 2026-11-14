# KIT VOX --- Complete Project Plan

> **Project:** Real-time voice assistant for Knotopian Institute of
> Technology (KIT), a dummy college.\
> **Architecture:** Custom offline speech recognition + deterministic
> multi-agent orchestration + secure college-tool execution.\
> **Core constraint:** No speech API keys, no cloud speech services, no
> pretrained speech-recognition or speech-synthesis models, and no
> browser speech-recognition API. Speech recognition and spoken output
> must be implemented using our own recordings, algorithms and locally
> generated audio.\
> **Status:** Working implementation plan. Verify the hackathon's
> written rules and the KIT API contract before deployment.

------------------------------------------------------------------------

## 1. Project objective

Build a voice-first college assistant that allows:

-   Prospective applicants to ask about courses, admissions,
    eligibility, fees and college information.
-   Students to retrieve attendance, timetable, holidays, examinations,
    requests and placement information.
-   Students to submit supported requests, such as leave or on-duty
    applications, after required information is collected and the user
    explicitly confirms.
-   Teachers to view pending requests and approve or reject a
    specifically identified request.
-   All user groups to ask questions answered from approved KIT
    documents and data sources.

The system should feel conversational while being honest about its
limitations. It must not claim to understand arbitrary speech if the
recognizer only supports a constrained vocabulary or phrase set.

### One-line description

> KIT VOX is a custom-built offline voice assistant that recognizes
> supported speech using MFCC and DTW, coordinates specialist software
> agents, enforces college policies in deterministic code, and securely
> executes authorized KIT operations.

### Non-goals for version 1

-   Open-domain, human-level conversation.
-   Unrestricted dictation.
-   A generative LLM.
-   Pretrained speech or language models.
-   Cloud speech-to-text or text-to-speech.
-   Autonomous actions without user confirmation.
-   Separate microservices for every agent.
-   Multi-language recognition unless explicitly required and properly
    tested.

------------------------------------------------------------------------

## 2. Non-negotiable constraints and decision gate

### 2.1 Speech restrictions

The implementation must not use:

-   Deepgram, AssemblyAI, Google Speech-to-Text, Azure Speech or any
    other hosted speech-recognition service.
-   Whisper, Vosk or other pretrained speech-recognition models, whether
    cloud-hosted or locally installed.
-   Browser Web Speech API recognition (`SpeechRecognition` /
    `webkitSpeechRecognition`).
-   Cloud TTS services or pretrained neural TTS models.
-   Browser `speechSynthesis` as a hidden fallback if the rule prohibits
    pretrained speech models or browser speech services.
-   Any speech API key.

Allowed implementation components, subject to organizer approval:

-   Browser microphone capture through `getUserMedia`, `MediaRecorder`
    or `AudioWorklet`.
-   NumPy and SciPy signal processing.
-   MFCC feature extraction implemented by the team.
-   DTW matching implemented by the team.
-   Team-recorded speech samples and templates.
-   Team-recorded response audio.
-   Concatenation of team-recorded phoneme, digit, number or phrase
    audio clips.
-   Custom rule-based / statistical intent and slot extraction.
-   KIT's provided college API and participant key, if permitted by the
    hackathon.

### 2.2 Important hackathon rule ambiguity

The supplied brief reportedly says to use a speech service while
prohibiting browser-built-in speech recognition. The later project
constraint says no speech service or pretrained speech model may be
used.

These instructions are not equivalent. Obtain written clarification from
the organizers before treating the custom recognizer as compliant.

Ask:

1.  Is a speech recognizer implemented from scratch using our own
    recordings, MFCC and DTW permitted?
2.  Are locally recorded audio templates permitted?
3.  Is locally assembled recorded-audio TTS permitted?
4.  Does the prohibition apply to browser-provided speech synthesis as
    well as browser speech recognition?
5.  Is the provided KIT college API allowed while speech APIs are
    prohibited?

**Default implementation while waiting:** build the from-scratch
recognizer and recorded-audio output. Do not add an external
speech-service adapter or a switch that could accidentally activate one.

### 2.3 KIT API key versus speech API key

The KIT participant key is used to access the supplied college backend.
It is not a speech API key. Keep it server-side in an environment
variable. Never place it in frontend code, source control, screenshots
or public logs.

If the organizers prohibit all external API calls, not just speech APIs,
clarify whether the supplied KIT API is an explicit exception.

------------------------------------------------------------------------

## 3. Product capabilities and user roles

  -----------------------------------------------------------------------
  User type                           Example capabilities
  ----------------------------------- -----------------------------------
  Public / applicant                  College information, courses,
                                      admissions, eligibility, brochure
                                      and application workflow

  Student                             Attendance, timetable, calendar,
                                      holidays, exams, requests,
                                      placements and permitted request
                                      submission

  Teacher                             Classes, pending requests, request
                                      details, approval and rejection

  All permitted users                 Supported voice commands, text
                                      fallback, conversation context and
                                      relevant knowledge retrieval
  -----------------------------------------------------------------------

The backend must determine the authenticated role from trusted
server-side session data and the KIT identity response. Never trust a
role, user ID or permission supplied by the browser or recognized
speech.

------------------------------------------------------------------------

## 4. Overall system architecture

``` text
                         KIT VOX WEB APP
                    React + Vite + TypeScript
                              |
                    Microphone / Text Input
                              |
                 Local Audio Capture and WAV
                              |
                 FastAPI Speech Endpoint
                              |
          +---------------------------------------+
          |       CUSTOM OFFLINE SPEECH ENGINE    |
          |                                       |
          |  Audio validation and resampling      |
          |       -> noise / VAD processing       |
          |       -> MFCC + delta features        |
          |       -> phrase or word DTW matching  |
          |       -> grammar constrained decode  |
          |       -> confidence / rejection       |
          +---------------------------------------+
                              |
                       Recognized Text
                              |
                 Custom NLU and Slot Extractor
                              |
                 Conversation State / Memory
                              |
                  MASTER ORCHESTRATOR AGENT
                              |
            +-----------------+------------------+
            |                 |                  |
       Student Agent     Teacher Agent      Admissions Agent
            |                 |                  |
       Knowledge Agent   Policy Agent      Knowledge Agent
            +-----------------+------------------+
                              |
                    Role and Policy Checks
                              |
                  Confirmation / Slot Filling
                              |
                    Authorized Tool Registry
                              |
                    KIT API / Local Documents
                              |
                 Verified Tool Result / Errors
                              |
                    Response Composition
                              |
               Recorded-Audio TTS Renderer
                              |
                   Audio + Visible Text Reply
                              |
                    SQLite Conversation Log
```

All agents run as modules/classes inside one FastAPI backend process for
version 1. This avoids distributed-system overhead and makes the project
easier to test and deploy.

------------------------------------------------------------------------

## 5. Multi-agent architecture

### 5.1 What "agent" means in this project

These are custom-built, deterministic, goal-directed software agents.
Each has a defined responsibility, state/context access, allowed tools
and decision logic. They are not LLM agents and must not be described as
autonomous generative agents.

Each agent should expose a small, consistent interface:

``` python
class BaseAgent:
    name: str

    def can_handle(self, intent, role) -> bool:
        ...

    def create_plan(self, intent, message, context):
        ...

    async def execute(self, plan, context):
        ...

    def format_response(self, result, context):
        ...
```

Use typed request/plan/result objects in the actual implementation
rather than passing arbitrary dictionaries everywhere.

### 5.2 Master Orchestrator Agent

Responsibilities:

-   Receive recognized text or typed input.
-   Read the authenticated role and conversation context.
-   Ask the NLU layer for intent and entities.
-   Select the appropriate specialist agent.
-   Manage multi-step workflows.
-   Preserve context across turns.
-   Ask for missing slots.
-   Route policy checks.
-   Require explicit confirmation for write operations.
-   Execute only permitted tools.
-   Inspect tool results and choose the next step.
-   Return a grounded response.

The orchestrator should not bypass role checks or execute arbitrary tool
names inferred from text.

### 5.3 Student Agent

Supported initial intents:

-   `GET_ATTENDANCE`
-   `GET_TIMETABLE`
-   `GET_HOLIDAYS`
-   `GET_EXAM_DATES`
-   `GET_MY_REQUESTS`
-   `SUBMIT_LEAVE`
-   `SUBMIT_ON_DUTY`
-   `GET_PLACEMENTS`
-   `REGISTER_PLACEMENT` (only if the KIT API supports it)
-   `CANCEL_REQUEST` (only if supported and confirmed)

Responsibilities:

-   Collect required date, reason, event and other required fields.
-   Read student data only through the authenticated student's KIT
    token.
-   Display the complete action summary before submission.
-   Ask for explicit confirmation.
-   Execute once and report the actual KIT result.

### 5.4 Teacher Agent

Supported initial intents:

-   `GET_TEACHER_CLASSES`
-   `LIST_PENDING`
-   `GET_REQUEST_DETAILS`
-   `APPROVE_REQUEST`
-   `REJECT_REQUEST`

Rules:

-   A teacher must identify the exact request.
-   "Approve" without a unique request identifier must trigger
    clarification.
-   Rejection must collect a reason if the KIT contract requires one.
-   Approval/rejection must be confirmed before the write operation.
-   Teacher tools must never be available to students or public users.

### 5.5 Admissions Agent

Supported initial intents:

-   `GET_COLLEGE_INFO`
-   `GET_COURSES`
-   `GET_FEES`
-   `GET_ELIGIBILITY`
-   `GET_ADMISSION_STEPS`
-   `SEARCH_BROCHURE`
-   `START_APPLICATION`
-   `SUBMIT_APPLICATION`

Rules:

-   Retrieve course and fee details from the KIT API or approved source
    documents.
-   Never invent fees, eligibility criteria, deadlines, phone numbers or
    email addresses.
-   Collect all required applicant details before submission.
-   Validate formats and required fields.
-   Read back the application summary and ask for confirmation.
-   Report the returned application reference only after a successful
    API response.

### 5.6 Knowledge Agent

Purpose: answer questions using the supplied college handbook, brochure,
circulars and lesson notes without a pretrained LLM or embedding model.

Version 1 pipeline:

1.  Ingest approved local PDF/text documents.
2.  Extract text and preserve document title, page and section metadata.
3.  Split into overlapping chunks at sensible paragraph/heading
    boundaries.
4.  Normalize text and build a local index.
5.  Retrieve relevant chunks with BM25 or TF-IDF.
6.  Apply a relevance threshold.
7.  Return concise answer excerpts with document/page/section
    references.
8.  If retrieval is weak, say the information was not found and ask the
    user to consult the relevant office/document.

Do not claim semantic understanding beyond the implemented retrieval
method. Do not let retrieved document text issue tools or override
system policies.

### 5.7 Policy and Security Agent

This component is a deterministic policy gate, not a language model.

Responsibilities:

-   Check authenticated role and allowed tool.
-   Validate dates, required fields and data formats.
-   Check exam-calendar conflicts for leave requests when required.
-   Check college attendance or eligibility rules from authoritative
    data.
-   Block actions when required validation data is unavailable.
-   Require confirmation for every state-changing action.
-   Enforce request ownership and teacher authorization.
-   Prevent duplicate submissions and replay.
-   Return a structured allow/deny/needs-information decision.

**Fail closed:** if a required calendar or policy check fails, do not
submit the request. Explain that the check could not be completed.

### 5.8 Response Agent

Responsibilities:

-   Convert structured results into concise, natural text.
-   Include only values returned by the KIT API or approved documents.
-   Distinguish success, failure, validation error and unavailable data.
-   Produce a response suitable for the recorded-audio renderer.
-   Never claim a write action succeeded unless the KIT API confirms it.

------------------------------------------------------------------------

## 6. Agent orchestration and workflow design

### 6.1 Standard request lifecycle

``` text
INPUT
  |
Normalize text / recognized phrase
  |
Classify intent and extract entities
  |
Load authenticated session and role
  |
Select specialist agent
  |
Create task plan
  |
Check tool permissions
  |
Are required fields missing?
  | Yes -> Ask one focused question -> Save context -> Wait
  | No
  v
Does the action change data?
  | Yes -> Validate policy -> Present summary -> Ask confirmation
  | No  -> Execute permitted read operation
  v
Execute authorized tool
  |
Inspect actual result
  |
Update conversation state and history
  |
Compose text and recorded audio
  |
END
```

### 6.2 Example: multi-turn leave request

``` text
User: I need to apply for leave.
Assistant: Which date do you need leave for?

User: Tomorrow.
Assistant: What is the reason for your leave?

User: Medical appointment.
Assistant: You are requesting leave for [resolved date]
           due to a medical appointment. Shall I submit it?

User: Yes.
Assistant: [Run final policy checks and submit once]
           Your leave request was submitted. Reference: [API result].
```

If the calendar cannot be checked, the assistant must not submit.

### 6.3 Pending action state

Persist a pending action with:

-   Unique pending-action ID.
-   Session/account owner.
-   Intent and tool name.
-   Validated slots.
-   Human-readable summary.
-   Creation and expiry time.
-   Confirmation status.
-   Idempotency key.
-   Relevant policy-check results.

On confirmation:

1.  Verify the pending action belongs to the current authenticated
    account/session.
2.  Verify it has not expired or already executed.
3.  Verify the confirmation refers to that pending action.
4.  Re-run critical policy checks.
5.  Execute with the same idempotency key for retries of that operation.
6.  Store the result and mark the action completed.
7.  Clear or close the pending state.

On cancellation, expire/clear the pending action without executing it.

A bare "yes" must not execute an action if there is no unique active
pending action.

### 6.4 Conversation context

Store structured context rather than relying only on transcript text.

Example:

``` json
{
  "active_agent": "student",
  "active_intent": "SUBMIT_LEAVE",
  "slots": {
    "date": "2026-11-15",
    "reason": "medical appointment"
  },
  "missing_slots": [],
  "pending_action_id": "server-generated-id",
  "awaiting": "confirmation"
}
```

Dates in examples are illustrative. Resolve relative dates using the
server's configured local timezone and the current date, not a hardcoded
date or UTC assumption.

------------------------------------------------------------------------

## 7. Speech recognition: fully custom, no pretrained models

### 7.1 Version 1 strategy

Start with phrase-level DTW for the most important commands. It is more
realistic under a short hackathon timeline than attempting unrestricted
word-level transcription immediately.

Example phrase templates:

-   "Show my attendance."
-   "Show my timetable."
-   "Show holidays."
-   "Show exam dates."
-   "Show my requests."
-   "I need leave."
-   "Apply for on duty."
-   "Show pending requests."
-   "Approve request."
-   "Reject request."
-   "What courses do you offer?"
-   "What are the admission requirements?"

Add separate constrained recognizers/grammars for follow-up values:

-   Yes / no / cancel.
-   Today / tomorrow.
-   Digits and supported numbers.
-   Month names and date patterns.
-   Common leave reasons and event names.

Expand to word-level recognition only after phrase-level end-to-end
performance is measured.

### 7.2 Audio capture

Frontend:

-   Request microphone access only after user action.
-   Use `getUserMedia`.
-   Capture PCM through AudioWorklet where feasible; MediaRecorder may
    be used if its output is decoded and normalized correctly.
-   Display microphone state and recording level.
-   Stop capture cleanly.
-   Send audio to the backend over the application's own HTTPS endpoint.
-   Keep text input visible at all times.

Do not use browser speech-recognition APIs.

### 7.3 Signal processing

Implement:

-   WAV validation.
-   Mono conversion.
-   Correct sample-rate conversion using `scipy.signal.resample_poly` or
    an equivalent correctly implemented resampler.
-   Amplitude normalization with clipping protection.
-   Optional pre-emphasis.
-   Frame blocking and windowing.
-   Noise-floor estimation.
-   Voice activity detection using adaptive thresholds.
-   Leading/trailing silence trimming.

Do not resample by simply selecting sample indices; that is not proper
anti-aliased resampling.

### 7.4 MFCC extraction

Suggested initial parameters for 16 kHz audio:

  Parameter                     Initial value
  ------------------- -----------------------
  Sample rate                       16,000 Hz
  FFT size                                512
  Frame length                          25 ms
  Hop length                            10 ms
  Mel filters                              26
  MFCC coefficients                        13
  Dynamic features      Delta and delta-delta

Implementation outline:

1.  Pre-emphasis.
2.  Split into overlapping frames.
3.  Apply Hamming window.
4.  Compute power spectrum.
5.  Apply a mel filterbank implemented by the team.
6.  Take log energies.
7.  Apply DCT.
8.  Retain MFCC coefficients.
9.  Calculate delta and delta-delta features.
10. Normalize features carefully.

Avoid normalizing every individual utterance in a way that removes
useful distinctions without evaluating the effect. Compare
feature-normalization choices empirically.

### 7.5 DTW matching

Implement dynamic time warping with:

-   A frame-level distance function such as cosine or Euclidean
    distance.
-   A Sakoe-Chiba band to limit pathological alignments.
-   Path-length normalization.
-   Multiple templates per phrase/word.
-   Best and second-best candidate scores.
-   Absolute rejection threshold calibrated on validation data.

Do not call `1 - best_distance / second_distance` a calibrated
probability. It is only a heuristic score unless calibrated against a
representative dataset.

Reject when: - No template is loaded. - Audio is too short or silent. -
Best distance exceeds a calibrated maximum. - Best and second-best
scores are too close. - The decoded sequence does not match an allowed
grammar.

### 7.6 Grammar-constrained decoding

The decoder maps recognized tokens/phrases to supported intents and
slots.

Example grammar:

``` text
GET_ATTENDANCE:
  "show my attendance"
  "what is my attendance"
  "attendance"

SUBMIT_LEAVE:
  "I need leave"
  "apply for leave"
  "submit leave"

CONFIRM:
  "yes"
  "confirm"

CANCEL:
  "no"
  "cancel"
```

Use explicit grammar patterns and slot parsers. Do not silently guess a
date or reason.

### 7.7 Data collection protocol

Record the team's own speech samples.

Recommended plan:

-   Start with 10--15 high-priority complete phrases.
-   Use at least 3 speakers if time permits.
-   Record multiple repetitions per phrase.
-   Vary speaking pace and natural intonation.
-   Record in a quiet room and then test in a realistic environment.
-   Store speaker, phrase, session and recording metadata.
-   Keep raw recordings out of Git if they contain personal voices or
    are large.
-   Use separate training and evaluation recordings.

Suggested dataset layout:

``` text
data/
  recordings/
    speaker_01/
      session_01/
        GET_ATTENDANCE/
        SUBMIT_LEAVE/
    speaker_02/
      session_01/
        GET_ATTENDANCE/
        SUBMIT_LEAVE/
  templates/
  evaluation/
```

### 7.8 Evaluation protocol

Never evaluate on the same utterances used to build templates.

Use speaker-independent testing:

-   Train on two speakers; test on the third.
-   Rotate the held-out speaker.
-   Also test a separate recording session where possible.
-   Report command accuracy, rejection rate, false-accept rate and
    confusion matrix.
-   Measure end-to-end latency from end of speech to displayed
    recognition result.

Gate for voice release:

  -----------------------------------------------------------------------
  Result                              Decision
  ----------------------------------- -----------------------------------
  Strong held-out performance and     Enable supported voice commands
  safe rejection                      

  Moderate performance                Reduce command vocabulary and
                                      retain text fallback

  Poor performance                    Keep voice as experimental; make
                                      text input the primary reliable
                                      path
  -----------------------------------------------------------------------

Set the numerical threshold only after measuring the dataset and
considering the cost of false commands. A wrong write action is more
serious than a rejected utterance.

------------------------------------------------------------------------

## 8. Offline speech output (TTS)

### 8.1 Version 1: team-recorded audio

Record reusable response phrases using a team member's voice.

Initial clips:

-   Greeting.
-   "I didn't catch that. Please try again."
-   "Please log in first."
-   "Which date do you mean?"
-   "What is the reason?"
-   "Do you want me to submit this?"
-   "Your request was submitted."
-   "I couldn't submit the request."
-   "That date conflicts with an examination."
-   "I couldn't verify the college calendar."
-   "Here are your pending requests."
-   "I couldn't find that information."

### 8.2 Dynamic values

For dynamic values such as attendance percentages, dates, request counts
and reference numbers, use one of:

1.  Pre-recorded digit/number/date components with carefully tested
    concatenation.
2.  Pre-recorded complete response variants for the small set of
    supported cases.
3.  Text-only response when the required value cannot be spoken
    naturally.

Audio concatenation can sound discontinuous. Test transitions, silence
boundaries, sample rate and loudness. Do not claim natural neural TTS.

### 8.3 TTS restrictions

-   No cloud TTS.
-   No pretrained neural TTS.
-   No browser `speechSynthesis` fallback unless organizers explicitly
    confirm it is allowed.
-   Keep visible text as the always-available response.
-   If the audio clip is missing, show text and explain that spoken
    output is unavailable.

------------------------------------------------------------------------

## 9. NLU, intent classification and slot extraction

No pretrained language model is used.

Use a small custom hybrid:

1.  Text normalization.
2.  Exact phrase matching for high-confidence commands.
3.  Token/keyword rules for supported variations.
4.  TF-IDF or another locally implemented statistical classifier if
    enough labelled examples exist.
5.  Entity extraction for dates, numbers, names, reasons and course
    codes.
6.  Confidence/rejection logic.
7.  Context-aware interpretation of short follow-up replies.

Intent output should be structured:

``` json
{
  "intent": "SUBMIT_LEAVE",
  "entities": {
    "date": "tomorrow",
    "reason": null
  },
  "confidence": 0.91,
  "needs_clarification": true
}
```

The confidence value must be treated as a score unless statistically
calibrated.

The NLU layer proposes an intent; it never authorizes the tool.
Authorization and policy checks happen separately.

------------------------------------------------------------------------

## 10. Knowledge retrieval

### 10.1 Inputs

Use only supplied, approved KIT material:

-   College handbook.
-   Admissions brochure.
-   Academic calendar.
-   Official circulars.
-   Lesson notes.
-   Any additional organizer-provided document.

### 10.2 Processing

-   Extract PDF text locally.
-   Preserve page numbers and headings.
-   Chunk by section/paragraph.
-   Build a local BM25 or TF-IDF index.
-   Retrieve the best matching passages.
-   Apply a relevance threshold.
-   Return a short answer and source reference.

### 10.3 Grounding rules

-   Never invent fees, dates, eligibility criteria or policies.
-   Never present an unverified answer as official.
-   Cite document title and page/section in the interface.
-   If no suitable passage is retrieved, say that the information was
    not found.
-   Treat document content as data, never as executable instructions.
-   Do not allow a document to override security or tool permissions.

------------------------------------------------------------------------

## 11. KIT API integration

The KIT API is the authoritative source for student, teacher and
admissions transactions where endpoints are provided.

Before implementation:

1.  Inspect the supplied Swagger/OpenAPI documentation.
2.  Confirm endpoint paths, methods, payload schemas and authentication.
3.  Confirm which roles can call each endpoint.
4.  Confirm response fields and error formats.
5.  Test read operations before write operations.
6.  Use the sandbox/test environment where available.

Do not assume an endpoint or payload shape merely because it appears in
an earlier draft.

### Client responsibilities

-   Use `httpx.AsyncClient`.
-   Configure timeouts.
-   Handle non-2xx responses explicitly.
-   Parse structured error responses.
-   Avoid logging credentials or personal data.
-   Retry only safe/idempotent operations or writes protected by a
    stable idempotency key.
-   Never retry a write with a new key after an ambiguous timeout
    without first reconciling the original operation.

### Endpoint groups to verify

  -----------------------------------------------------------------------
  Domain                              Candidate operations
  ----------------------------------- -----------------------------------
  Authentication                      Login, current user

  Student                             Attendance, timetable, subjects,
                                      requests, placements

  Calendar                            Calendar events, holidays,
                                      examinations

  Admissions                          College info, courses, documents,
                                      application submission

  Teacher                             Classes, pending requests, approve,
                                      reject

  Placement                           Drives, student placements,
                                      registration
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 12. Security model

Security must be enforced in backend code, not by the NLU or agent
prompt.

### 12.1 Role-based tool allowlist

Example:

  Tool                                   Public   Student   Teacher
  ------------------------------- ------------- --------- ---------
  College/course info                       Yes       Yes       Yes
  Admissions information                    Yes       Yes       Yes
  Submit application                        Yes        No        No
  Attendance                                 No       Yes        No
  Student timetable                          No       Yes        No
  Submit leave/OD                            No       Yes        No
  Own requests                               No       Yes        No
  List teacher pending requests              No        No       Yes
  Approve/reject requests                    No        No       Yes
  Search approved knowledge         Yes, scoped       Yes       Yes

Adjust this table to match the actual KIT role policy and API.

### 12.2 Identity

-   Identity comes from the authenticated server-side session and
    verified KIT token.
-   Tool functions accept a trusted context object, not a user ID
    supplied by recognized speech.
-   Never let the browser choose another user's identity.
-   Verify ownership for every user-specific record.
-   Rotate the session ID after login.
-   Invalidate the session on logout.
-   Use secure, HTTP-only cookies in production.
-   Use appropriate SameSite and CSRF protections.

### 12.3 Write actions

Every state-changing action must:

1.  Pass role authorization.
2.  Have all required slots.
3.  Pass deterministic policy validation.
4.  Show a summary.
5.  Receive explicit confirmation.
6.  Use an idempotency key.
7.  Record the final result.
8.  Return success only if the API confirms success.

### 12.4 Session and history isolation

-   Public history must not expose authenticated history.
-   Authenticated history must be scoped to the account.
-   Switching accounts must not reveal the previous account's
    transcript.
-   Pending actions must be scoped to the owning account and session.
-   Do not store passwords in conversation history.
-   Minimize retention of sensitive personal data.

### 12.5 Secrets

-   KIT participant key only in backend environment.
-   KIT access tokens stored securely and never sent to frontend
    storage.
-   `.env` excluded from Git.
-   Redact secrets from logs and errors.
-   Rotate any key that has been exposed in chat, screenshots or source
    control.

------------------------------------------------------------------------

## 13. Backend API design

Suggested application endpoints:

  -----------------------------------------------------------------------
  Route                               Purpose
  ----------------------------------- -----------------------------------
  `POST /api/session`                 Create or resume a session

  `POST /api/login`                   Authenticate with KIT

  `POST /api/logout`                  End session and clear pending
                                      action

  `GET /api/me`                       Return current authenticated
                                      role/profile

  `POST /api/asr`                     Run custom offline speech
                                      recognition

  `POST /api/turn`                    Process text or recognized speech
                                      through orchestrator

  `POST /api/confirm`                 Confirm a specific pending action

  `POST /api/cancel`                  Cancel a specific pending action

  `GET /api/history`                  Return history scoped to current
                                      account/session

  `GET /api/public/info`              Public college information

  `GET /api/health`                   Readiness and subsystem health

  `GET /api/audio/{clip}`             Serve approved recorded response
                                      audio
  -----------------------------------------------------------------------

Use request/response schemas and validate every field. The exact routes
can be adjusted to the existing frontend, but confirmation should
identify a specific pending action rather than relying on an ambiguous
intent string.

------------------------------------------------------------------------

## 14. Database design

Use SQLite for the hackathon version.

Suggested tables:

### `sessions`

-   `id`
-   `role`
-   `login_id`
-   `display_name`
-   `kit_token` (only if necessary; protect it)
-   `created_at`
-   `expires_at`
-   `last_seen_at`

### `conversation_turns`

-   `id`
-   `session_id`
-   `account_id` (nullable for public)
-   `user_text`
-   `assistant_text`
-   `intent`
-   `agent`
-   `created_at`

### `conversation_state`

-   `session_id`
-   `state_json`
-   `updated_at`

### `pending_actions`

-   `id`
-   `session_id`
-   `account_id`
-   `tool_name`
-   `intent`
-   `slots_json`
-   `summary`
-   `idempotency_key`
-   `status`
-   `expires_at`
-   `result_json`

### `knowledge_chunks`

Optional persistent local index metadata:

-   `id`
-   `document_id`
-   `page_number`
-   `section`
-   `chunk_text`

For a short-lived demo, the document index may instead be built at
startup from local files.

------------------------------------------------------------------------

## 15. Suggested repository structure

``` text
kit-vox/
├── PLAN.md
├── README.md
├── .gitignore
├── render.yaml
├── backend/
│   ├── requirements.txt
│   ├── .env.example
│   ├── config.py
│   ├── app.py
│   ├── db.py
│   ├── schemas.py
│   ├── session_manager.py
│   ├── security/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── permissions.py
│   │   └── policy.py
│   ├── asr/
│   │   ├── __init__.py
│   │   ├── audio_io.py
│   │   ├── resample.py
│   │   ├── vad.py
│   │   ├── mfcc.py
│   │   ├── dtw.py
│   │   ├── templates.py
│   │   ├── grammar.py
│   │   ├── phrase_recognizer.py
│   │   └── pipeline.py
│   ├── nlu/
│   │   ├── normalize.py
│   │   ├── intents.py
│   │   ├── entities.py
│   │   └── router.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── orchestrator.py
│   │   ├── student_agent.py
│   │   ├── teacher_agent.py
│   │   ├── admissions_agent.py
│   │   ├── knowledge_agent.py
│   │   ├── policy_agent.py
│   │   └── response_agent.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── registry.py
│   │   ├── student.py
│   │   ├── teacher.py
│   │   └── public.py
│   ├── knowledge/
│   │   ├── ingest.py
│   │   ├── chunk.py
│   │   ├── index.py
│   │   └── retrieve.py
│   ├── tts/
│   │   ├── render.py
│   │   ├── concatenate.py
│   │   └── manifest.json
│   └── tests/
│       ├── test_audio.py
│       ├── test_mfcc.py
│       ├── test_dtw.py
│       ├── test_asr_eval.py
│       ├── test_nlu.py
│       ├── test_agents.py
│       ├── test_workflows.py
│       ├── test_tools.py
│       ├── test_security.py
│       └── test_history_isolation.py
├── data/
│   ├── vocabulary.json
│   ├── recordings/          # local, normally gitignored
│   ├── templates/           # generated locally
│   ├── tts/                 # team-recorded audio
│   └── documents/           # approved KIT source documents
├── scripts/
│   ├── record_phrases.py
│   ├── build_templates.py
│   ├── evaluate_asr.py
│   └── ingest_documents.py
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── styles.css
│       ├── lib/
│       │   ├── api.ts
│       │   ├── audio_capture.ts
│       │   └── audio_playback.ts
│       ├── components/
│       │   ├── VoiceWidget.tsx
│       │   ├── TextFallback.tsx
│       │   └── ConfirmationPanel.tsx
│       └── pages/
│           ├── Home.tsx
│           ├── Assistant.tsx
│           └── History.tsx
└── docs/
    ├── architecture.md
    └── adr/
        ├── 001-custom-offline-asr.md
        ├── 002-agent-orchestration.md
        ├── 003-server-side-identity.md
        ├── 004-deterministic-policy-enforcement.md
        └── 005-recorded-audio-output.md
```

------------------------------------------------------------------------

## 16. Implementation order and time management

The original plan's 12-hour schedule should not be treated as
guaranteed. The actual event deadline takes priority. Build a working
vertical slice first.

### Phase 0 --- Rule and API verification

-   Obtain written clarification about custom offline speech
    recognition.
-   Verify that the KIT API is permitted.
-   Inspect the KIT Swagger/OpenAPI schemas.
-   Confirm the available test accounts and roles.
-   Confirm the event submission deadline.

**Exit condition:** No unresolved assumption about whether the planned
speech approach is permitted.

### Phase 1 --- Minimal speech proof

-   Capture a microphone recording.
-   Convert to a known PCM/WAV format.
-   Implement MFCC.
-   Record a small set of command phrases.
-   Implement DTW matching.
-   Print best candidate and distance.
-   Add rejection for silence/unknown speech.

**Exit condition:** A small held-out test set recognizes the initial
command phrases reliably enough to proceed.

### Phase 2 --- First end-to-end vertical slice

Implement one read-only student command:

``` text
Speak -> Recognize -> Intent -> Student Agent
      -> Permission Check -> KIT Attendance API
      -> Response -> Recorded Audio / Text
```

**Exit condition:** A logged-in test student can ask for attendance and
receive the actual KIT response.

### Phase 3 --- Orchestrator and state

-   Add base agent interface.
-   Add master orchestrator.
-   Add student agent.
-   Add context persistence.
-   Add missing-slot questions.
-   Add pending-action storage.

**Exit condition:** Multi-turn leave request collects date and reason
without losing context.

### Phase 4 --- Policy and write operation

-   Add calendar validation.
-   Fail closed when validation cannot be completed.
-   Present a full action summary.
-   Confirm a specific pending action.
-   Use stable idempotency for retries.
-   Store the actual result.

**Exit condition:** A valid test request submits once; a
rejected/failed/cancelled request never falsely reports success.

### Phase 5 --- Teacher and public flows

-   Add teacher read operations.
-   Add request selection and confirmation.
-   Add admissions/course information.
-   Add application slot collection only if time permits.

**Exit condition:** Each enabled operation respects its role and actual
KIT API result.

### Phase 6 --- Knowledge and response audio

-   Ingest one or two important approved documents.
-   Build local keyword/BM25 retrieval.
-   Return source references.
-   Record common audio phrases.
-   Add dynamic digit/date clips only if quality is acceptable.

**Exit condition:** A question with a known answer retrieves a cited
source; unknown questions produce an honest fallback.

### Phase 7 --- Security, tests and demo

-   Test cross-account history isolation.
-   Test role escalation.
-   Test confirmation replay.
-   Test duplicate submissions.
-   Test calendar failure.
-   Test microphone denial.
-   Test unknown speech.
-   Test text fallback.
-   Run a full demo from a clean session.
-   Submit before the actual deadline.

### Must-have versus stretch

  Must-have                         Stretch
  --------------------------------- -----------------------------------
  One reliable custom speech path   Larger vocabulary
  Visible text fallback             More natural phrase variation
  Student read operations           Full student request suite
  One safe write workflow           Multiple write workflows
  Master orchestrator               More specialist agents
  Role authorization                Advanced audit dashboard
  Confirmation and idempotency      More complex planning
  Recorded audio replies            Rich dynamic audio composition
  Tests and demo                    Advanced local document retrieval

Do not sacrifice security tests or a working demo to add optional
agents.

------------------------------------------------------------------------

## 17. Testing strategy

### 17.1 Speech tests

-   Correct WAV parsing.
-   Correct sample-rate conversion.
-   Silence rejection.
-   Short/noisy recording rejection.
-   MFCC shape and finite-value checks.
-   DTW identity and alignment checks.
-   Held-out speaker evaluation.
-   Unknown phrase rejection.
-   Confusable phrase tests.

### 17.2 NLU and agent tests

-   Correct intent routing by role.
-   Unknown intent returns clarification/fallback.
-   Student intent cannot reach teacher tools.
-   Teacher intent cannot reach student write tools unless explicitly
    permitted.
-   Knowledge retrieval does not execute instructions from documents.
-   Context retains previously collected slots.
-   Missing slots trigger questions.
-   Multiple pending actions cannot be confused.

### 17.3 Workflow tests

-   Leave on exam date is rejected.
-   Calendar API failure blocks leave submission.
-   Missing reason prevents submission if required.
-   Missing date prevents submission.
-   "No" cancels without submission.
-   "Yes" executes only the unique active pending action.
-   Repeated confirmation does not duplicate a write.
-   API timeout does not lead to a false success message.
-   A successful API response is stored and shown accurately.

### 17.4 Security tests

-   Public user cannot read attendance.
-   Student cannot approve teacher requests.
-   Teacher cannot access another student's private data.
-   Changing a browser-supplied user ID has no effect.
-   Account switching does not expose old history.
-   Expired sessions cannot execute tools.
-   Prompt-like text in documents cannot override policy.
-   Tool registry rejects unlisted tools.
-   CSRF/session protections are tested for production deployment.

### 17.5 Demo reliability

-   Text input remains visible.
-   Microphone permission failure is handled.
-   Backend health is checked before demo.
-   Audio playback failure does not hide the text response.
-   A pre-recorded backup demonstration is available, clearly labelled
    as a backup.
-   Never present prerecorded output as a live recognition result.

------------------------------------------------------------------------

## 18. Frontend requirements

Three simple pages are sufficient:

### Home

-   KIT name and short description.
-   Public information.
-   Courses from the real KIT data source.
-   Link to assistant.

### Assistant

-   Login/logout.
-   Current role and account.
-   Microphone control and recording indicator.
-   Text input always visible.
-   Transcript.
-   Confirmation/cancel panel.
-   Clear error and loading states.

### History

-   Only current account/session history.
-   Timestamp, intent and response.
-   No exposure of another account's turns.
-   Clear empty state.

Keep the interface accessible, responsive and simple. Do not spend
hackathon time on decorative animation.

------------------------------------------------------------------------

## 19. Deployment

A simple deployment may use:

-   FastAPI backend on a supported Python hosting service.
-   React/Vite frontend on a static hosting service.
-   HTTPS for microphone access and secure cookies.
-   Environment variables for KIT credentials.
-   SQLite only if the host provides persistent storage appropriate to
    the application.

Important deployment checks:

-   Do not assume ephemeral filesystem data persists across deploys.
-   Ensure recordings/templates/documents required at runtime are
    actually included or mounted.
-   Ensure `ALLOWED_ORIGINS` is explicitly configured.
-   Do not use wildcard CORS with credentials.
-   Set secure cookie settings in production.
-   Confirm audio response paths work after deployment.
-   Test cold starts and microphone permissions.
-   Keep participant credentials out of client bundles and logs.

If deployment is unreliable, a tested local demo is preferable to a
broken public URL.

------------------------------------------------------------------------

## 20. Demo script

### 0:00--0:20 --- Project and constraint

"This is KIT VOX. It uses a speech recognizer implemented from scratch
with our own recordings, MFCC and DTW. It does not depend on pretrained
speech models or speech API keys. A custom orchestrator coordinates
role-specific agents and deterministic college rules."

### 0:20--0:45 --- Public information

Ask: "What courses do you offer?"

Show the retrieved course list and speak a recorded response if
available.

### 0:45--1:15 --- Student read flow

Log in as a test student.

Ask: "Show my attendance."

Show the actual KIT API response and the agent's spoken/text reply.

### 1:15--1:45 --- Multi-turn write flow

Ask: "I need leave."

Provide a date and reason over multiple turns.

Show the summary and confirmation. Confirm only if the test environment
and data make it safe.

### 1:45--2:05 --- Policy rejection

Use a known exam date in the test calendar.

Show that the request is blocked by deterministic Python validation, not
by a conversational suggestion.

### 2:05--2:25 --- Teacher flow

Log in as a test teacher.

List pending requests, select a specific request and demonstrate the
confirmation-protected approval/rejection flow if available.

### 2:25--2:45 --- Architecture and measurements

Show:

-   Agent orchestration diagram.
-   Speech pipeline.
-   Measured held-out recognition results.
-   Security and workflow test results.
-   Honest limitations and next steps.

Never claim an untested feature is complete.

------------------------------------------------------------------------

## 21. Architecture decision records (ADRs)

Write short records for significant decisions.

### ADR 001 --- Custom offline speech recognition

**Decision:** Use team-recorded samples, MFCC and DTW.\
**Reason:** No pretrained speech models or speech services are permitted
by the project constraint.\
**Trade-off:** Constrained vocabulary and reduced robustness compared
with large-scale neural ASR.\
**Validation:** Held-out speaker evaluation and unknown-phrase
rejection.

### ADR 002 --- Deterministic multi-agent orchestration

**Decision:** Implement specialist Python agents coordinated by a master
orchestrator.\
**Reason:** Clear separation of responsibilities without a pretrained
LLM or external inference service.\
**Trade-off:** The system handles explicitly implemented workflows
rather than open-ended autonomous reasoning.\
**Validation:** Agent routing, multi-turn workflow and tool-permission
tests.

### ADR 003 --- Server-side identity

**Decision:** Derive identity from the authenticated server-side session
and KIT token.\
**Reason:** User-supplied IDs must not control access to private
records.\
**Trade-off:** Session management and token lifecycle must be
implemented carefully.\
**Validation:** Cross-account and role-escalation tests.

### ADR 004 --- Deterministic policy enforcement

**Decision:** Enforce examination conflicts, required fields,
authorization and confirmation in backend code.\
**Reason:** Important college rules must not depend on probabilistic
text interpretation.\
**Trade-off:** Every supported rule must be explicitly implemented and
tested.\
**Validation:** Policy unit tests and failure-path tests.

### ADR 005 --- Recorded-audio speech output

**Decision:** Use team-recorded clips and controlled audio composition.\
**Reason:** Avoid cloud TTS and pretrained speech synthesis.\
**Trade-off:** Limited phrasing and potentially noticeable audio joins.\
**Validation:** Test every supported response and dynamic value.

------------------------------------------------------------------------

## 22. Risk register

  -----------------------------------------------------------------------
  Risk                    Impact                  Mitigation
  ----------------------- ----------------------- -----------------------
  Organizer rule          Compliance failure      Written clarification
  ambiguity                                       before claiming
                                                  compliance

  Custom ASR weak         Voice commands fail     Reduce vocabulary,
  accuracy                                        improve recordings,
                                                  retain text input

  Speaker overfitting     Poor real-world         Speaker-independent
                          recognition             evaluation

  Noisy demo venue        False recognition       Noise testing,
                                                  push-to-talk, rejection
                                                  threshold

  Missing KIT schema      Tool calls fail         Verify Swagger and test
  details                                         payloads

  Calendar API failure    Unsafe leave approval   Fail closed

  Confirmation state bug  Wrong or duplicate      Persist pending action
                          action                  and test replay

  Account history leakage Privacy breach          Account-scoped queries
                                                  and isolation tests

  Teacher role            Unauthorized access     Use verified
  misclassification                               role/permissions, not
                                                  endpoint success
                                                  heuristics

  Audio template missing  No spoken reply         Visible text fallback

  Dynamic audio sounds    Unclear response        Use short clips or
  poor                                            text-only fallback

  Exposed participant key Sandbox compromise      Server-only secrets and
                                                  key rotation

  Ephemeral deployment    Lost history/templates  Persistent storage or
  storage                                         documented limitation

  Scope creep             Incomplete submission   Must-have/stretch
                                                  separation
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 23. Scope discipline

Do not build these during the initial hackathon version:

-   A generative LLM.
-   Neural ASR trained from scratch without sufficient data/time.
-   A custom formant synthesizer.
-   Unrestricted dictation.
-   Multiple languages.
-   Separate agent microservices.
-   Kubernetes or complex infrastructure.
-   A large analytics dashboard.
-   Real-time partial transcription.
-   Advanced semantic embeddings requiring pretrained models.
-   Unverified college policy answers.
-   Autonomous write operations without confirmation.

The goal is a complete, safe, demonstrable vertical slice.

------------------------------------------------------------------------

## 24. Final release checklist

### Rules and constraints

-   [ ] Organizer clarification recorded.
-   [ ] No speech API key or hosted speech recognition.
-   [ ] No pretrained speech-recognition model.
-   [ ] No browser speech recognition.
-   [ ] TTS approach confirmed compliant.
-   [ ] KIT API use confirmed permitted.

### Speech

-   [ ] Microphone capture works.
-   [ ] WAV parsing and resampling tested.
-   [ ] MFCC implementation tested.
-   [ ] DTW implementation tested.
-   [ ] Phrase templates built from team recordings.
-   [ ] Held-out evaluation completed.
-   [ ] Unknown speech rejected safely.
-   [ ] Text fallback always visible.

### Agents and workflows

-   [ ] Master orchestrator implemented.
-   [ ] Specialist agents have clear responsibilities.
-   [ ] Role-based routing works.
-   [ ] Context persists between turns.
-   [ ] Missing fields are collected.
-   [ ] Pending actions are stored securely.
-   [ ] Confirmation and cancellation work.
-   [ ] Policy checks fail closed.
-   [ ] Tool results are checked before reporting success.

### Security

-   [ ] Server-side identity.
-   [ ] Role-based tool allowlist.
-   [ ] Account-specific history.
-   [ ] Secure session lifecycle.
-   [ ] Stable idempotency for writes.
-   [ ] Secrets excluded from Git and frontend.
-   [ ] Red-team tests pass.

### Demo and submission

-   [ ] One public flow works.
-   [ ] One student read flow works.
-   [ ] One multi-turn workflow works.
-   [ ] One policy rejection works.
-   [ ] Teacher flow works if included.
-   [ ] Spoken output works or text fallback is clear.
-   [ ] README includes architecture and measured results.
-   [ ] Limitations are documented honestly.
-   [ ] Demo is tested from a clean session.
-   [ ] Submission is completed before the official deadline.

------------------------------------------------------------------------

## 25. Future improvements after the hackathon

If more time and data become available:

1.  Expand phrase-level DTW to more flexible word/phoneme recognition.
2.  Improve speaker robustness and acoustic normalization.
3.  Add streaming recognition with partial results.
4.  Improve local document retrieval and ranking.
5.  Add more specialist agents only where a distinct workflow requires
    them.
6.  Improve recorded-audio composition and prosody.
7.  Add stronger audit logging and administrative controls.
8.  Evaluate every new feature with a separate test set.

Do not promise these future capabilities as features of version 1.

------------------------------------------------------------------------

## 26. Final engineering principles

1.  **No speech API dependency:** voice input and output are built from
    local algorithms and team-created recordings.
2.  **No pretrained speech models:** no hidden model dependency is
    permitted.
3.  **Agents are explicit:** every agent has a responsibility, context,
    permitted tools and testable behavior.
4.  **The orchestrator coordinates; it does not bypass security.**
5.  **Policies are deterministic:** important college rules are enforced
    in code.
6.  **Identity is server-side:** recognized words cannot select another
    user's account.
7.  **Writes require confirmation:** no silent submissions, approvals or
    rejections.
8.  **Fail safely:** unavailable validation must never be treated as
    approval.
9.  **Ground every answer:** use actual KIT results or approved
    documents.
10. **Measure rather than claim:** report real recognition and workflow
    test results.
11. **Text fallback is always available.**
12. **Finish a reliable vertical slice before expanding scope.**

**Final positioning:** KIT VOX is not an LLM chatbot. It is a custom
offline voice interface connected to a deterministic, multi-agent
college workflow engine. Its differentiators are from-scratch speech
processing, explicit agent orchestration, secure tool execution, policy
enforcement and measurable reliability.
