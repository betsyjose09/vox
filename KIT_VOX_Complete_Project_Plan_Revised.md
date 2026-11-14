# KIT VOX --- Complete Project Plan (Revised)

**Project:** Real-time voice assistant for Knotopian Institute of
Technology (KIT), a dummy college\
**Architecture:** Custom offline, constrained-vocabulary speech
recognition + deterministic orchestration + secure college-tool
execution\
**Document status:** Revised engineering plan; implementation must be
checked against the organizers' written rules and the actual KIT API
contract.

> **Important compliance gate:** The supplied challenge brief says to
> use a speech service while prohibiting the browser's built-in
> speech-recognition API. This plan assumes a stricter project
> constraint: no speech API keys, no hosted speech services, no
> pretrained ASR/TTS models, and no browser speech-recognition or
> speech-synthesis fallback. These interpretations are not automatically
> equivalent. Obtain written organizer approval before claiming the
> custom speech path is compliant.

------------------------------------------------------------------------

## 1. Project objective

Build a voice-first web assistant that supports three user groups:

-   **Prospective applicants:** ask about KIT, courses, admissions,
    eligibility, fees, required documents and dates; submit an
    application only if the supplied API supports it.
-   **Students:** retrieve their own attendance, timetable, holidays,
    examination dates, requests and placement information; submit
    supported leave or on-duty (OD) requests.
-   **Teachers:** view requests they are authorized to review and
    approve or reject a specifically identified request when the KIT API
    supports that operation.

All user groups can ask questions answered from approved KIT documents
and API data.

The assistant must be conversational within its supported capabilities,
but honest about limitations. A constrained recognizer must not be
presented as unrestricted dictation or human-level speech understanding.

### One-line description

**KIT VOX is a custom-built, constrained-vocabulary offline voice
assistant that recognizes supported speech using team-created audio
templates and signal-processing algorithms, routes requests through
deterministic specialist modules, enforces policy and authorization in
backend code, and securely executes permitted KIT operations.**

### Version 1 non-goals

-   Open-domain, human-level conversation.
-   Unrestricted dictation or arbitrary natural-language transcription.
-   A generative LLM.
-   Pretrained speech or language models.
-   Cloud speech-to-text or text-to-speech.
-   Browser Web Speech API recognition or browser speech synthesis.
-   Autonomous state-changing actions without explicit confirmation.
-   A separate microservice for every specialist module.
-   Multi-language recognition unless explicitly required and
    independently tested.

------------------------------------------------------------------------

## 2. Non-negotiable constraints and decision gate

### 2.1 Speech restrictions assumed by this plan

Do not use:

-   Deepgram, AssemblyAI, Google Speech-to-Text, Azure Speech or another
    hosted ASR service.
-   Whisper, Vosk or another pretrained ASR model, whether hosted or
    locally installed.
-   `SpeechRecognition` or `webkitSpeechRecognition`.
-   Cloud TTS services or pretrained neural TTS models.
-   `speechSynthesis` as a fallback unless organizers explicitly confirm
    it is allowed.
-   Any speech API key.

Potentially permissible components, subject to organizer approval:

-   Browser microphone capture using `getUserMedia`, `MediaRecorder` or
    `AudioWorklet`.
-   Team-implemented signal processing using NumPy and SciPy.
-   MFCC feature extraction implemented by the team.
-   DTW matching implemented by the team.
-   Audio templates recorded by the team.
-   Team-recorded response audio and concatenation of team-recorded
    clips.
-   Custom rule-based or statistical intent and slot extraction.
-   The supplied KIT college API and participant key, if permitted.

Microphone capture is not speech recognition: `getUserMedia` only
obtains audio. Recognition must happen in the team's own backend
implementation.

### 2.2 Written clarification required

The challenge description reportedly asks teams to use a speech service,
while the project constraint prohibits speech services and pretrained
speech models. These requirements conflict unless the organizers have
clarified that a from-scratch recognizer is an acceptable substitute.

Ask the organizers in writing:

1.  Is a speech recognizer implemented by the team using its own
    recordings, MFCC and DTW permitted?
2.  Are locally recorded speech templates permitted?
3.  Is locally assembled recorded-audio TTS permitted?
4.  Does the restriction cover browser-provided speech synthesis as well
    as browser speech recognition?
5.  Is the supplied KIT college API permitted, including its participant
    key?
6.  Are public raw speech datasets allowed for training, provided no
    pretrained model is used?
7.  Are general-purpose numerical, signal-processing and ML libraries
    allowed if model weights are initialized and trained by the team?

**Default while waiting:** implement the custom recognizer and
team-recorded audio output. Do not add an external speech adapter or a
hidden browser speech fallback. Do not claim compliance until the
organizers confirm the interpretation.

### 2.3 KIT API key versus speech API key

The KIT participant key is for the supplied college backend; it is not a
speech API key. Keep it server-side in an environment variable. Never
place it in frontend code, source control, screenshots or public logs.

If the organizers prohibit all external API calls rather than only
speech services, clarify whether the supplied KIT API is an explicit
exception.

------------------------------------------------------------------------

## 3. Product capabilities and roles

  -----------------------------------------------------------------------
  User type                           Initial capabilities
  ----------------------------------- -----------------------------------
  Public / applicant                  College information, courses,
                                      admissions, eligibility, fees,
                                      brochure retrieval and application
                                      workflow if supported

  Student                             Own attendance, timetable,
                                      holidays, exam dates, own requests,
                                      placement information and supported
                                      leave/OD submission

  Teacher                             Authorized classes, pending
                                      requests, request details and
                                      approval/rejection if supported

  All permitted users                 Supported voice commands, text
                                      input fallback, conversation
                                      context and approved knowledge
                                      retrieval
  -----------------------------------------------------------------------

The backend determines role and identity from trusted server-side
authentication state and verified KIT identity data. Never trust a role,
user ID, student ID or permission supplied by the browser or recognized
speech.

### Capability principle

Every feature is enabled only when all three are true:

1.  The actual KIT API contract supports it.
2.  The authenticated role is authorized to use it.
3.  The complete workflow has been implemented and tested.

Do not invent endpoints, request payloads, response fields or
permissions.

------------------------------------------------------------------------

## 4. Overall system architecture

``` text
                         KIT VOX WEB APP
                    React + Vite + TypeScript
                              |
                   Microphone / Text Input
                              |
                  Local Audio Capture (PCM/WAV)
                              |
                    FastAPI Speech Endpoint
                              |
              CUSTOM OFFLINE SPEECH RECOGNIZER
              - Audio validation and resampling
              - Voice activity / silence detection
              - MFCC and optional delta features
              - DTW phrase/template matching
              - Constrained grammar and slot parsing
              - Confidence/rejection thresholds
                              |
                       Recognized Text
                              |
                  Custom NLU / Slot Extractor
                              |
                  Conversation State Manager
                              |
                     MASTER ORCHESTRATOR
                              |
             +----------------+----------------+
             |                |                |
        Student Module   Teacher Module   Admissions Module
             |                |                |
             +----------------+----------------+
                              |
                    Knowledge Retrieval Module
                              |
                  Authorization + Policy Gate
                              |
                    Confirmation / Slot Filling
                              |
                    Allowlisted Tool Registry
                              |
                    KIT API / Local Documents
                              |
                  Verified Result / Error State
                              |
                    Response Composer
                              |
               Team-Recorded Audio Renderer
                              |
                   Audio + Visible Text Reply
                              |
                  SQLite Conversation History
```

All modules run in one FastAPI backend process for version 1. This
avoids distributed-system overhead and makes the project easier to test
and deploy.

**Important separation:** the speech recognizer proposes text; NLU
proposes intent and slots; specialist modules plan supported work; the
security and policy layer decides whether an operation is permitted. No
model prediction or agent decision grants authorization.

------------------------------------------------------------------------

## 5. Multi-agent / specialist-module architecture

### 5.1 What "agent" means in this project

These are deterministic, goal-directed software modules. Each has a
defined responsibility, supported intents, context access and permitted
tools. They are not LLM agents and must not be described as autonomous
generative agents.

Use typed request, plan and result objects rather than arbitrary
dictionaries.

Illustrative interface:

``` python
class BaseAgent:
    name: str

    def can_handle(self, intent: str, role: str) -> bool:
        ...

    def create_plan(self, request, context):
        ...

    async def execute(self, plan, context):
        ...

    def format_response(self, result, context):
        ...
```

The policy/security layer should be a shared deterministic service, not
an autonomous agent.

### 5.2 Master Orchestrator

Responsibilities:

-   Receive recognized text or typed input.
-   Load authenticated role and conversation context.
-   Ask NLU to classify intent and extract entities.
-   Select the appropriate specialist module.
-   Manage multi-turn workflows and missing slots.
-   Route read operations through the tool registry.
-   Route writes through policy validation and explicit confirmation.
-   Inspect actual tool results.
-   Update conversation state and history.
-   Return a grounded response.

The orchestrator must not execute arbitrary tool names inferred from
user text.

### 5.3 Student module

Candidate intents, subject to the API contract:

-   `GET_ATTENDANCE`
-   `GET_TIMETABLE`
-   `GET_HOLIDAYS`
-   `GET_EXAM_DATES`
-   `GET_MY_REQUESTS`
-   `SUBMIT_LEAVE`
-   `SUBMIT_ON_DUTY`
-   `GET_PLACEMENTS`
-   `REGISTER_PLACEMENT` (only if supported)
-   `CANCEL_REQUEST` (only if supported)

Responsibilities:

-   Collect required date, reason, event and other mandatory fields.
-   Read student data only through the authenticated student's verified
    KIT context.
-   Show the complete action summary before submission.
-   Require explicit confirmation.
-   Execute once using the verified tool contract.
-   Report the actual KIT API result, not an assumed success.

### 5.4 Teacher module

Candidate intents:

-   `GET_TEACHER_CLASSES`
-   `LIST_PENDING`
-   `GET_REQUEST_DETAILS`
-   `APPROVE_REQUEST`
-   `REJECT_REQUEST`

Rules:

-   A teacher must identify one specific request.
-   "Approve" without a unique request must trigger clarification.
-   Collect a rejection reason if the API contract requires one.
-   Confirm every state-changing approval/rejection.
-   Teacher tools must never be exposed to students or public users.
-   The API and backend authorization rules remain authoritative.

### 5.5 Admissions module

Candidate intents:

-   `GET_COLLEGE_INFO`
-   `GET_COURSES`
-   `GET_FEES`
-   `GET_ELIGIBILITY`
-   `GET_ADMISSION_STEPS`
-   `SEARCH_BROCHURE`
-   `START_APPLICATION`
-   `SUBMIT_APPLICATION`

Rules:

-   Retrieve courses, fees and eligibility from the KIT API or approved
    official documents.
-   Never invent fees, eligibility criteria, deadlines, contact details
    or seat counts.
-   Collect all required applicant fields before submission.
-   Validate formats and required fields.
-   Read back the application summary and require confirmation.
-   Return an application reference only after a successful API
    response.

### 5.6 Knowledge retrieval module

Purpose: answer questions using the supplied handbook, brochure,
circulars and lesson notes without pretrained LLMs or embedding models.

Version 1 pipeline:

1.  Ingest approved local PDF/text documents.
2.  Extract text and preserve document title, page and section metadata.
3.  Split at headings and paragraph boundaries, with limited overlap.
4.  Normalize text and build a local BM25 or TF-IDF index.
5.  Retrieve relevant passages.
6.  Apply a relevance threshold.
7.  Return short extracted passages or carefully controlled templates
    with document/page references.

If retrieval is weak, say the information was not found. Do not
fabricate an answer.

BM25 and TF-IDF retrieve text; they do not provide unrestricted semantic
understanding or generative reasoning. Lesson explanations should be
limited to what can be supported by retrieved notes and deterministic
templates.

Treat document content as data, never as executable instructions.
Retrieved content cannot override system policy or trigger tools.

### 5.7 Policy and security service

This is deterministic backend code, not an LLM or autonomous agent.

Responsibilities:

-   Check authenticated role and allowed tool.
-   Validate required fields and formats.
-   Check exam-calendar conflicts for leave requests when required by
    the rulebook/API.
-   Apply attendance and eligibility rules using authoritative data.
-   Block actions when required validation data is unavailable.
-   Require confirmation for every state-changing action.
-   Enforce request ownership and teacher authorization.
-   Prevent duplicate submissions and confirmation replay.
-   Return structured decisions: `ALLOW`, `DENY` or `NEEDS_INFORMATION`.

**Fail closed:** if a required calendar or policy check fails, do not
submit. Explain which check could not be completed.

### 5.8 Response composer

Responsibilities:

-   Convert structured results into concise text.
-   Include only values returned by the KIT API or approved documents.
-   Distinguish success, failure, validation error and unavailable data.
-   Produce text suitable for the recorded-audio renderer.
-   Never claim a write succeeded unless the KIT API confirms success.

------------------------------------------------------------------------

## 6. Orchestration and workflow lifecycle

### 6.1 Standard request lifecycle

``` text
Audio or typed input
        |
Audio validation / text normalization
        |
Speech recognition (audio only)
        |
Intent classification + entity extraction
        |
Load authenticated session and role
        |
Select specialist module
        |
Create typed task plan
        |
Role and tool permission check
        |
Are required fields missing?
   | Yes -> Ask one focused question -> Persist context -> Wait
   | No
   v
Is this a state-changing operation?
   | No -> Execute permitted read operation
   | Yes
   v
Run deterministic policy checks
        |
Present complete action summary
        |
Obtain explicit confirmation
        |
Revalidate action and authorization
        |
Execute allowlisted tool
        |
Verify actual KIT result
        |
Update state and history
        |
Compose text + optional recorded audio
```

### 6.2 Example: multi-turn leave request

``` text
User: I need to apply for leave.
Assistant: Which date do you need leave for?

User: Tomorrow.
Assistant: What is the reason for your leave?

User: Medical appointment.
Assistant: You are requesting leave for [resolved date]
           because of a medical appointment. Shall I submit it?

User: Yes.
Assistant: [Revalidate pending action and policy, then submit once]
           Your leave request was submitted. Reference: [API result].
```

If the calendar cannot be checked, the assistant must not submit.

### 6.3 Pending action state machine

Persist a pending action with:

-   Server-generated pending-action ID.
-   Owning session and authenticated account.
-   Intent and allowlisted tool identifier.
-   Validated slots.
-   Human-readable summary.
-   Creation and expiry timestamps.
-   Confirmation status.
-   Stable idempotency key.
-   Relevant policy-check results.
-   Execution status and final API result, when available.

Suggested states:

``` text
PENDING
   |
VALIDATING
   | failure -> DENIED
   v
READY_FOR_CONFIRMATION
   | user cancels -> CANCELLED
   | expires -> EXPIRED
   | confirms
   v
EXECUTING
   | confirmed success -> SUCCEEDED
   | confirmed failure -> FAILED
   | ambiguous timeout -> UNKNOWN
                         |
                         v
                    RECONCILING
                    /    |     \
              SUCCESS  FAILED  UNKNOWN
```

On confirmation:

1.  Verify the pending action belongs to the current account/session.
2.  Verify it is unexpired and has not already executed.
3.  Verify the confirmation refers to that exact pending-action ID.
4.  Re-run critical authorization and policy checks.
5.  Execute using the same idempotency key for retries of the same
    operation, if the KIT API supports idempotency.
6.  Store the actual result and mark the action complete.
7.  Clear or close the pending state.

A bare "yes" must not execute an action if there is no unique active
pending action.

### 6.4 Exactly-once limitation

A local idempotency key does **not** guarantee exactly-once execution
against an external API unless the KIT API supports idempotency or
provides a reliable way to reconcile the result.

If the API request times out after it may have succeeded:

-   Mark the operation `UNKNOWN`.
-   Query the KIT API for the matching request/reference if a lookup
    endpoint exists.
-   Do not blindly retry with a new key.
-   If reconciliation is unavailable, stop and report that the outcome
    could not be verified.

### 6.5 Conversation context

Store structured context, not only transcript text.

Example:

``` json
{
  "active_module": "student",
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

Dates are illustrative. Resolve relative dates using the server's
configured college timezone and current date, never a hardcoded date or
assumed UTC date.

------------------------------------------------------------------------

## 7. Custom offline speech recognition

### 7.1 Honest capability definition

MFCC + DTW phrase matching is a valid **constrained-vocabulary template
recognizer**. It is not unrestricted speech-to-text and does not
automatically transcribe arbitrary reasons, names or sentences.

Version 1 should recognize a deliberately small command set and
supported follow-up vocabulary. For unsupported free-form details,
retain the visible text input.

### 7.2 Version 1 strategy

Start with phrase-level DTW for high-priority commands.

Example command phrases:

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

Build separate constrained recognizers/grammars for:

-   Yes / no / cancel.
-   Today / tomorrow.
-   Supported digits and numbers.
-   Month names and supported date forms.
-   A small set of common reasons and event labels, if collected and
    tested.

Expand vocabulary only after measuring held-out performance.

### 7.3 Audio capture

Frontend:

-   Request microphone access only after a user action.
-   Use `getUserMedia`.
-   Capture PCM through `AudioWorklet` where feasible.
-   `MediaRecorder` may be used if its encoded output is decoded and
    normalized correctly.
-   Display microphone state and recording level.
-   Stop capture cleanly.
-   Send audio to the backend over the application's HTTPS endpoint.
-   Keep text input visible at all times.

Do not use browser speech-recognition APIs.

### 7.4 Signal processing

Implement:

-   WAV validation and safe size/duration limits.
-   Mono conversion.
-   Correct anti-aliased sample-rate conversion, such as
    `scipy.signal.resample_poly`.
-   Amplitude normalization with clipping protection.
-   Optional pre-emphasis.
-   Frame blocking and windowing.
-   Noise-floor estimation.
-   Voice activity detection using adaptive thresholds.
-   Leading/trailing silence trimming.

Do not resample by merely selecting every nth sample; that causes
aliasing.

### 7.5 MFCC extraction

Suggested starting parameters for 16 kHz audio:

  Parameter                             Initial value
  ------------------- -------------------------------
  Sample rate                               16,000 Hz
  FFT size                                        512
  Frame length                                  25 ms
  Hop length                                    10 ms
  Mel filters                                      26
  MFCC coefficients                                13
  Dynamic features      Delta; optionally delta-delta

Implementation:

1.  Optional pre-emphasis.
2.  Split signal into overlapping frames.
3.  Apply Hamming window.
4.  Compute power spectrum.
5.  Apply a team-implemented mel filterbank.
6.  Take log filterbank energies.
7.  Apply DCT.
8.  Retain selected MFCC coefficients.
9.  Calculate delta features if evaluation supports them.
10. Apply feature normalization selected through validation.

Do not assume one normalization method is best. Compare options
empirically and ensure the method does not remove useful distinctions.

### 7.6 DTW matching

Implement:

-   Frame-level distance, such as cosine or Euclidean distance.
-   Sakoe--Chiba band to limit pathological alignments.
-   Path-length-normalized distance.
-   Multiple templates per phrase.
-   Best and second-best candidate distances.
-   Absolute rejection threshold calibrated on held-out validation data.

Do not call `1 - best_distance / second_distance` a calibrated
probability. It is only a heuristic unless calibrated against
representative data.

Reject the input when:

-   No template is loaded.
-   Audio is too short, clipped or silent.
-   Best distance exceeds a calibrated maximum.
-   Best and second-best candidates are too close.
-   The recognized phrase does not match an allowed grammar.

### 7.7 Dynamic slot limitation

Phrase-level DTW identifies known phrases. It does not automatically
recognize arbitrary speech between phrases.

For leave reasons, applicant names and detailed descriptions, use one
of:

1.  Text fallback (recommended for version 1).
2.  A constrained vocabulary recorded and evaluated by the team.
3.  A separately implemented word-level recognizer, only if there is
    enough data and time.

Do not silently guess a date, name, reason or event.

### 7.8 Data collection

Record the team's own speech samples.

Recommended protocol:

-   Start with 10--15 high-priority complete phrases.
-   Use at least three speakers if feasible.
-   Record multiple repetitions per phrase.
-   Vary speaking pace and natural intonation.
-   Record in a quiet room, then test in realistic background noise.
-   Store speaker, phrase, session and recording metadata.
-   Keep raw recordings out of Git if they contain personal voices or
    are large.
-   Keep training and evaluation recordings separate.

Suggested layout:

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

### 7.9 Evaluation

Never evaluate only on the utterances used to create templates.

Use speaker-independent evaluation:

-   Train/build templates using two speakers and test on a third.
-   Rotate the held-out speaker.
-   If possible, also hold out a separate recording session.
-   Report command accuracy, false-accept rate, rejection rate and
    confusion matrix.
-   Measure end-of-speech-to-recognition latency and
    end-of-speech-to-response latency.

Release gate:

  -----------------------------------------------------------------------
  Result                              Decision
  ----------------------------------- -----------------------------------
  Good held-out performance and safe  Enable supported voice commands
  rejection                           

  Moderate performance                Reduce vocabulary; retain text
                                      fallback

  Poor performance                    Keep voice experimental; make text
                                      the reliable path
  -----------------------------------------------------------------------

Choose thresholds based on measured data and the cost of false
acceptance. A wrong write command is more serious than a rejected
utterance.

### 7.10 If organizers require an actual trained speech model

DTW template matching is custom algorithmic recognition, but it is not
conventional parametric model training.

If the judges explicitly require a trained ML model, add a small model
trained from random initialization using team-collected labelled data. A
compact CNN over MFCC features can classify a fixed set of commands.
This is **audio command classification**, not general-purpose ASR.

A custom-trained command classifier still will not transcribe arbitrary
leave reasons or names. Keep the constrained grammar/text fallback.

Do not add a neural model merely for appearance. It must have
speaker-independent evaluation and must not use pretrained weights.

------------------------------------------------------------------------

## 8. Offline spoken output

### 8.1 Version 1: team-recorded audio

Record reusable response phrases in a consistent voice and recording
environment.

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

For attendance percentages, dates, counts and reference numbers, use:

1.  Complete recorded response variants for common cases.
2.  Recorded sentence templates with dynamic number/date clips.
3.  Individual recorded digits/number components only if the result
    remains understandable.

Example:

-   "Your attendance is" --- one clip.
-   "82" --- one clip.
-   "percent" --- one clip.

Normalize sample rate, loudness and silence boundaries. Test joins;
concatenated clips may sound discontinuous.

If the required value cannot be spoken clearly, return the visible text
response without pretending audio was generated.

### 8.3 TTS restrictions

-   No cloud TTS.
-   No pretrained neural TTS.
-   No browser `speechSynthesis` fallback unless explicitly approved.
-   Keep visible text as an always-available response.
-   If an audio clip is missing or playback fails, show text and
    indicate spoken output is unavailable.

Do not describe recorded-clip concatenation as natural neural TTS.

------------------------------------------------------------------------

## 9. NLU, intent classification and slot extraction

No pretrained language model is used.

Use a small hybrid:

1.  Text normalization.
2.  Exact phrase matching for high-confidence commands.
3.  Keyword and grammar rules for supported variations.
4.  A custom-trained statistical intent classifier if enough labelled
    examples exist.
5.  Entity extraction for supported dates, numbers, course codes and
    known vocabulary.
6.  Confidence/rejection logic.
7.  Context-aware interpretation of short follow-up replies.

### 9.1 Recommended trained intent classifier

If the competition expects evidence of model training, train a small
text classifier from scratch:

``` text
Training examples
       |
Text normalization
       |
Word / character TF-IDF features
       |
Logistic Regression (trained by the team)
       |
Intent score distribution
       |
Rejection threshold
       |
Orchestrator
```

This is a trained intent classifier, not a speech-recognition model. Do
not confuse the two.

Create labelled examples for each supported intent, including
paraphrases and negative/ambiguous examples. Split train/validation/test
data before tuning. Report macro-F1 and per-intent precision/recall.

Example structured output:

``` json
{
  "intent": "SUBMIT_LEAVE",
  "entities": {
    "date": "tomorrow",
    "reason": null
  },
  "score": 0.91,
  "needs_clarification": true
}
```

The score is not a calibrated probability unless calibration has been
measured.

The NLU layer proposes intent and slots; it never authorizes a tool.

------------------------------------------------------------------------

## 10. Knowledge retrieval

### 10.1 Approved inputs

-   College handbook.
-   Admissions brochure.
-   Academic calendar.
-   Official circulars.
-   Lesson notes.
-   Other organizer-provided official documents.

### 10.2 Processing

1.  Extract PDF text locally.
2.  Preserve page numbers, headings and document title.
3.  Chunk by section and paragraph.
4.  Build a local BM25 or TF-IDF index.
5.  Retrieve candidate passages.
6.  Apply a relevance threshold.
7.  Return short evidence-backed answers with source references.

### 10.3 Grounding rules

-   Never invent fees, dates, eligibility, policies or contact details.
-   Never present an unverified answer as official.
-   Cite document title and page/section in the interface.
-   If no suitable passage is retrieved, say it was not found.
-   Treat document text as data, not executable instructions.
-   Never allow retrieved text to override authorization or policy.
-   For policy-sensitive questions, prefer the authoritative
    handbook/API and show the source.

------------------------------------------------------------------------

## 11. KIT API integration

The supplied KIT API is authoritative for student, teacher and
admissions transactions where endpoints are provided.

Before implementation:

1.  Inspect supplied Swagger/OpenAPI documentation.
2.  Confirm endpoint paths, methods, payload schemas and authentication.
3.  Confirm role permissions for each endpoint.
4.  Confirm response fields and error formats.
5.  Test read operations before write operations.
6.  Use the sandbox/test environment where available.

Do not assume endpoint names or payload structures from this plan.

### 11.1 Backend API client

Use `httpx.AsyncClient` with:

-   Explicit connect/read/write timeouts.
-   Non-2xx handling.
-   Structured error parsing.
-   Safe logging with sensitive fields redacted.
-   Retries only for safe/idempotent reads or writes protected by
    API-supported idempotency.
-   Reconciliation after ambiguous write timeouts.

Never retry an ambiguous write with a new idempotency key before
checking whether the original operation succeeded.

### 11.2 Candidate endpoint groups to verify

  -----------------------------------------------------------------------
  Domain                              Candidate operations
  ----------------------------------- -----------------------------------
  Authentication                      Login, current user

  Student                             Attendance, timetable, subjects,
                                      requests, placements

  Calendar                            Events, holidays, examinations

  Admissions                          College info, courses, documents,
                                      application submission

  Teacher                             Classes, pending requests, approve,
                                      reject

  Placement                           Drives, registration
  -----------------------------------------------------------------------

These are discovery categories, not claims that the endpoints exist.

------------------------------------------------------------------------

## 12. Security model

Security must be enforced in backend code, not by NLU or agent
instructions.

### 12.1 Role-based tool allowlist

Illustrative matrix; adjust to the actual KIT role policy and API:

  -------------------------------------------------------------------------
  Tool                         Public            Student            Teacher
  ---------------- ------------------ ------------------ ------------------
  College/course                  Yes                Yes                Yes
  information                                            

  Admissions                      Yes                Yes                Yes
  information                                            

  Submit                          Yes                 No                 No
  application                                            

  Attendance                       No   Own records only Only if explicitly
                                                                  permitted

  Student                          No   Own records only Only if explicitly
  timetable                                                       permitted

  Submit leave/OD                  No   Own account only                 No

  Own requests                     No   Own records only                 No

  List teacher                     No                 No   Authorized scope
  pending requests                                                     only

  Approve/reject                   No                 No         Authorized
  requests                                                    requests only

  Search approved       Public-scoped                Yes                Yes
  knowledge                                              
  -------------------------------------------------------------------------

### 12.2 Identity

-   Derive identity from authenticated server-side session and verified
    KIT token.
-   Never let browser-supplied IDs choose another user's identity.
-   Verify ownership for every user-specific record.
-   Rotate session ID after login.
-   Invalidate session on logout.
-   Use secure, HTTP-only cookies in production.
-   Configure SameSite and CSRF protections.
-   Enforce session expiry and revocation.

### 12.3 Write actions

Every state-changing action must:

1.  Pass role authorization.
2.  Have all required slots.
3.  Pass deterministic policy validation.
4.  Show a complete summary.
5.  Receive explicit confirmation tied to a specific pending-action ID.
6.  Use API-supported idempotency where available.
7.  Record the final result.
8.  Return success only if the API confirms success.

### 12.4 History and session isolation

-   Public history must not expose authenticated history.
-   Authenticated history must be scoped to the verified account.
-   Switching accounts must not reveal the previous account's
    transcript.
-   Pending actions must be scoped to the owning account and session.
-   Do not store passwords in conversation history.
-   Minimize retention of personal data.

### 12.5 Secrets and tokens

-   KIT participant key stays server-side in environment variables.
-   Do not send KIT access tokens to frontend storage.
-   Do not store raw tokens in plaintext SQLite fields.
-   If persistence is necessary, use an appropriate secret/encryption
    mechanism and restrict access.
-   Exclude `.env` from Git.
-   Redact credentials from logs and errors.
-   Rotate any key exposed in chat, screenshots or source control.

------------------------------------------------------------------------

## 13. Backend application endpoints

Suggested application routes:

  -----------------------------------------------------------------------
  Route                               Purpose
  ----------------------------------- -----------------------------------
  `POST /api/session`                 Create or resume session

  `POST /api/login`                   Authenticate with KIT

  `POST /api/logout`                  End session and clear pending state

  `GET /api/me`                       Return current authenticated
                                      role/profile

  `POST /api/asr`                     Run custom offline recognition

  `POST /api/turn`                    Process text or recognized speech
                                      through orchestrator

  `POST /api/actions/{id}/confirm`    Confirm a specific pending action

  `POST /api/actions/{id}/cancel`     Cancel a specific pending action

  `GET /api/history`                  Return history scoped to current
                                      account/session

  `GET /api/public/info`              Public college information

  `GET /api/health`                   Readiness and subsystem health

  `GET /api/audio/{clip}`             Serve approved recorded response
                                      audio
  -----------------------------------------------------------------------

Use validated request/response schemas. The exact routes can change to
fit the frontend, but confirmation must identify a specific pending
action rather than relying on an ambiguous intent string.

------------------------------------------------------------------------

## 14. Database design

SQLite is appropriate for a hackathon prototype if the hosting
environment provides persistent storage and expected concurrency is low.
For production or higher concurrency, reassess the database choice.

Suggested tables:

### `sessions`

-   `id`
-   `account_id` (nullable for public)
-   `role`
-   `display_name`
-   secure token reference or encrypted token field only if necessary
-   `created_at`
-   `expires_at`
-   `last_seen_at`
-   `revoked_at`

### `conversation_turns`

-   `id`
-   `session_id`
-   `account_id` (nullable for public)
-   `user_text`
-   `assistant_text`
-   `intent`
-   `module`
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
-   `created_at`
-   `updated_at`

### `audit_events`

-   `id`
-   `session_id`
-   `account_id`
-   `event_type`
-   `tool_name`
-   `outcome`
-   redacted metadata
-   `created_at`

Do not store passwords or unnecessary sensitive audio/transcripts.
Consider SQLite WAL mode, transactions and database backups. Confirm
that the deployment filesystem is persistent; otherwise history may
disappear after restart or redeploy.

The document index can be rebuilt at startup from local approved files,
or its metadata can be stored separately.

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
│   │   ├── auth.py
│   │   ├── permissions.py
│   │   └── policy.py
│   ├── asr/
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
│   │   ├── classifier.py
│   │   └── router.py
│   ├── agents/
│   │   ├── base.py
│   │   ├── orchestrator.py
│   │   ├── student.py
│   │   ├── teacher.py
│   │   ├── admissions.py
│   │   ├── knowledge.py
│   │   └── response.py
│   ├── tools/
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
│   ├── recordings/       # local; normally gitignored
│   ├── templates/        # generated locally
│   ├── tts/              # team-recorded audio
│   └── documents/         # approved KIT source documents
├── scripts/
│   ├── record_phrases.py
│   ├── build_templates.py
│   ├── evaluate_asr.py
│   ├── train_intent.py
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
        ├── 002-deterministic-orchestration.md
        ├── 003-server-side-identity.md
        ├── 004-deterministic-policy-enforcement.md
        └── 005-recorded-audio-output.md
```

------------------------------------------------------------------------

## 16. Implementation order and time management

Do not treat a proposed schedule as guaranteed. The official submission
deadline and actual remaining time take priority.

Build a working vertical slice before expanding scope.

### Phase 0 --- Rules and API verification

-   Obtain written clarification about custom offline speech recognition
    and TTS.
-   Verify that KIT API use is permitted.
-   Inspect Swagger/OpenAPI schemas.
-   Confirm test accounts and roles.
-   Confirm official submission deadline and timezone.

**Exit condition:** no unresolved assumption about whether the chosen
speech approach is permitted, and enough API information to implement
one real read operation.

### Phase 1 --- Minimal speech proof

-   Capture a microphone recording.
-   Convert to known PCM/WAV format.
-   Implement MFCC.
-   Record a small set of command phrases.
-   Implement DTW matching.
-   Print best candidate and distance.
-   Add rejection for silence and unknown speech.

**Exit condition:** a held-out test set recognizes the initial command
phrases at a measured, acceptable level.

### Phase 2 --- First end-to-end vertical slice

Implement one read-only student command:

``` text
Speak
  -> Recognize
  -> Intent
  -> Student module
  -> Permission check
  -> KIT attendance API
  -> Verify result
  -> Text + recorded audio response
```

**Exit condition:** a logged-in test student asks for attendance and
receives the actual KIT API result.

### Phase 3 --- Orchestrator and state

-   Add specialist module interface.
-   Add master orchestrator.
-   Add student module.
-   Add context persistence.
-   Add missing-slot questions.
-   Add pending-action storage.

**Exit condition:** a multi-turn leave request collects date and reason
without losing context.

### Phase 4 --- Policy and write operation

-   Add calendar validation.
-   Fail closed when validation cannot be completed.
-   Present full action summary.
-   Confirm a specific pending action.
-   Use stable idempotency where supported.
-   Reconcile ambiguous outcomes.
-   Store actual result.

**Exit condition:** a valid test request submits once; rejected, failed
or cancelled requests never falsely report success.

### Phase 5 --- Teacher and public flows

-   Add teacher read operations.
-   Add specific request selection and confirmation.
-   Add admissions/course information.
-   Add application slot collection only if time permits and the API
    supports it.

**Exit condition:** every enabled operation respects the actual API
contract and role permissions.

### Phase 6 --- Knowledge and response audio

-   Ingest the most important approved documents.
-   Build local keyword/BM25 retrieval.
-   Return source references.
-   Record common response phrases.
-   Add dynamic number/date clips only if quality is acceptable.

**Exit condition:** a known question retrieves a cited source; unknown
questions produce an honest fallback.

### Phase 7 --- Security, tests and demo

Test:

-   Cross-account history isolation.
-   Role escalation.
-   Confirmation replay.
-   Duplicate submissions.
-   Calendar failure.
-   Microphone denial.
-   Unknown speech.
-   Text fallback.
-   API timeout and reconciliation.
-   Clean-session end-to-end demo.

Submit before the official deadline.

### Must-have versus stretch

  -----------------------------------------------------------------------
  Must-have                           Stretch
  ----------------------------------- -----------------------------------
  One reliable custom constrained     Larger vocabulary
  speech path                         

  Visible text fallback               More phrase variations

  Student read operation              Full student service catalogue

  One safe leave or OD workflow       Multiple write workflows

  Role authorization                  More specialist modules

  Confirmation and cancellation       More complex planning

  Saved, account-scoped history       Advanced audit interface

  Recorded audio replies or clear     More natural audio composition
  text fallback                       

  Working tests and demo              Neural command classifier if
                                      time/data permit

  Verified KIT API integration        Placement registration and
                                      admissions submission
  -----------------------------------------------------------------------

Do not sacrifice security tests or a working demo to add optional
agents.

------------------------------------------------------------------------

## 17. Testing strategy

### 17.1 Speech tests

-   Correct WAV parsing.
-   Correct sample-rate conversion.
-   Silence rejection.
-   Short/noisy/clipped recording rejection.
-   MFCC shape and finite-value checks.
-   DTW identity and alignment checks.
-   Held-out speaker evaluation.
-   Unknown phrase rejection.
-   Confusable phrase tests.
-   End-of-speech-to-result latency.

### 17.2 NLU and module tests

-   Correct intent routing by role.
-   Unknown intent returns clarification/fallback.
-   Student intent cannot reach teacher tools.
-   Teacher intent cannot reach unauthorized student write tools.
-   Knowledge retrieval cannot execute document instructions.
-   Context retains collected slots.
-   Missing slots trigger focused questions.
-   Multiple pending actions cannot be confused.

### 17.3 Workflow tests

-   Leave on an exam date is rejected when the authoritative calendar
    confirms the conflict.
-   Calendar API failure blocks leave submission when the check is
    mandatory.
-   Missing reason prevents submission if required.
-   Missing date prevents submission.
-   "No" cancels without submission.
-   "Yes" executes only the unique active pending action.
-   Repeated confirmation does not duplicate a write.
-   API timeout does not lead to false success.
-   Ambiguous write outcomes enter reconciliation.
-   Successful API response is stored and shown accurately.

### 17.4 Security tests

-   Public user cannot read attendance.
-   Student cannot approve teacher requests.
-   Teacher cannot access unauthorized student data.
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
-   Audio playback failure does not hide text response.
-   A prerecorded backup demonstration is available and clearly
    labelled.
-   Never present prerecorded output as a live recognition result.

------------------------------------------------------------------------

## 18. Frontend requirements

Three simple pages are sufficient.

### Home

-   KIT name and short introduction.
-   Public college information.
-   Courses from the actual KIT data source or approved brochure.
-   Link to the public assistant.

### Assistant

-   Login/logout for student and teacher.
-   Current role/account indicator.
-   Microphone control and recording indicator.
-   Text input always visible.
-   Transcript.
-   Confirmation/cancel panel.
-   Clear loading, error and unavailable states.

### History

-   Only current account/session history.
-   Timestamp, intent and response.
-   Empty state.
-   No exposure of another account's turns.

Keep the interface accessible, responsive and simple. Fancy animation is
not a priority.

------------------------------------------------------------------------

## 19. Deployment

Possible deployment:

-   FastAPI backend on a supported Python hosting service.
-   React/Vite frontend on a static hosting service.
-   HTTPS for microphone access and secure cookies.
-   Environment variables for KIT credentials.
-   SQLite only if the host provides persistent storage appropriate to
    the application.

Deployment checks:

-   Do not assume ephemeral filesystem data persists.
-   Ensure templates and documents needed at runtime are packaged or
    mounted.
-   Configure allowed origins explicitly.
-   Do not use wildcard CORS with credentials.
-   Set secure cookie settings in production.
-   Test audio response paths after deployment.
-   Test cold starts and microphone permissions.
-   Keep participant credentials out of client bundles and logs.
-   If deployment is unreliable, use a tested local demo rather than a
    broken public URL.

------------------------------------------------------------------------

## 20. Demo script

A concise demo should prove real behavior rather than list planned
features.

### 0:00--0:20 --- Project and constraints

"This is KIT VOX. It uses a constrained speech recognizer implemented by
our team using our own recordings, MFCC and DTW. A deterministic
orchestrator coordinates role-specific workflows, and backend code
enforces permissions and college rules."

Only say this if the implementation and organizer interpretation support
the claim.

### 0:20--0:45 --- Public information

Ask: "What courses do you offer?"

Show the actual retrieved course list and play a recorded response if
available.

### 0:45--1:15 --- Student read flow

Log in as a test student.

Ask: "Show my attendance."

Show the actual KIT API response and the assistant's text/audio reply.

### 1:15--1:45 --- Multi-turn write flow

Ask: "I need leave."

Provide a supported date and reason.

Show the summary and confirmation. Submit only in the designated test
environment.

### 1:45--2:05 --- Policy rejection

Use an exam date confirmed by the test calendar.

Show that deterministic backend validation blocks the request.

### 2:05--2:25 --- Teacher flow

Log in as a test teacher. List pending requests, select one specific
request and demonstrate confirmation-protected approval/rejection if
supported.

### 2:25--2:45 --- Architecture and measurements

Show:

-   Speech pipeline.
-   Orchestration diagram.
-   Held-out recognition measurements.
-   Security/workflow test results.
-   Honest limitations.

Never claim an untested feature is complete.

------------------------------------------------------------------------

## 21. Architecture decision records

### ADR 001 --- Custom constrained offline speech recognition

**Decision:** Use team-recorded samples, team-implemented MFCC and DTW
for a constrained command vocabulary.

**Reason:** Avoid pretrained speech models and hosted speech services
under the assumed project constraint.

**Trade-off:** Limited vocabulary and lower robustness than large-scale
neural ASR. This is not unrestricted dictation.

**Validation:** Held-out speaker evaluation, false-accept measurement
and unknown-phrase rejection.

### ADR 002 --- Deterministic orchestration

**Decision:** Implement a master orchestrator and specialist Python
modules.

**Reason:** Clear responsibility separation without a pretrained LLM or
external inference service.

**Trade-off:** The system supports explicitly implemented workflows
rather than open-ended autonomous reasoning.

**Validation:** Routing, multi-turn workflow and tool-permission tests.

### ADR 003 --- Server-side identity

**Decision:** Derive identity from authenticated server-side session and
verified KIT token.

**Reason:** User-supplied IDs must not control access to private
records.

**Trade-off:** Session lifecycle and token handling must be implemented
carefully.

**Validation:** Cross-account and role-escalation tests.

### ADR 004 --- Deterministic policy enforcement

**Decision:** Enforce examination conflicts, required fields,
authorization and confirmation in backend code.

**Reason:** Important college rules must not depend on probabilistic
text interpretation.

**Trade-off:** Each supported rule must be explicitly implemented and
tested.

**Validation:** Policy unit tests and failure-path tests.

### ADR 005 --- Recorded-audio output

**Decision:** Use team-recorded clips and controlled audio composition.

**Reason:** Avoid cloud TTS and pretrained speech synthesis.

**Trade-off:** Limited phrasing and potentially noticeable audio joins.

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
                                                  improve recordings,
                                                  retain text fallback

  Speaker overfitting     Poor real-world         Speaker-independent
                          recognition             evaluation

  Noisy demo venue        False recognition       Push-to-talk, noise
                                                  testing, rejection
                                                  thresholds

  Missing KIT schema      Tool calls fail         Verify Swagger and test
                                                  payloads

  Calendar API failure    Unsafe leave submission Fail closed

  Confirmation state bug  Wrong or duplicate      Persist pending action
                          action                  and test replay

  API timeout after write Unknown transaction     Reconcile; do not
                          outcome                 blindly retry

  Account history leakage Privacy breach          Account-scoped queries
                                                  and isolation tests

  Teacher role            Unauthorized operation  Trust verified identity
  misclassification                               and permissions, not
                                                  NLU

  Missing audio template  No spoken reply         Visible text fallback

  Poor clip joins         Unclear audio           Test joins; use
                                                  complete phrase clips
                                                  or text fallback

  Exposed participant key Sandbox compromise      Server-only secrets and
                                                  key rotation

  Ephemeral deployment    Lost history/templates  Persistent storage or
                                                  documented limitation

  Scope creep             Incomplete submission   Must-have/stretch
                                                  separation
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 23. Scope discipline

Do not build these during the initial version:

-   Generative LLM.
-   Neural ASR trained from scratch without sufficient data/time.
-   Custom formant synthesizer.
-   Unrestricted dictation.
-   Multiple languages.
-   Separate agent microservices.
-   Kubernetes or complex infrastructure.
-   Large analytics dashboard.
-   Pretrained semantic embeddings.
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
-   [ ] Dataset and ML-library restrictions confirmed.

### Speech

-   [ ] Microphone capture works.
-   [ ] WAV parsing and resampling tested.
-   [ ] MFCC implementation tested.
-   [ ] DTW implementation tested.
-   [ ] Phrase templates built from team recordings.
-   [ ] Held-out evaluation completed.
-   [ ] Unknown speech rejected safely.
-   [ ] Text fallback always visible.
-   [ ] Audio output uses only approved team-created recordings.

### Orchestration and workflows

-   [ ] Master orchestrator implemented.
-   [ ] Specialist modules have clear responsibilities.
-   [ ] Role-based routing works.
-   [ ] Context persists between turns.
-   [ ] Missing fields are collected.
-   [ ] Pending actions are stored securely.
-   [ ] Confirmation and cancellation work.
-   [ ] Policy checks fail closed.
-   [ ] Tool results are checked before reporting success.
-   [ ] Ambiguous write outcomes are reconciled or reported as unknown.

### Security

-   [ ] Server-side identity.
-   [ ] Role-based tool allowlist.
-   [ ] Account-specific history.
-   [ ] Secure session lifecycle.
-   [ ] Idempotency used where supported by the KIT API.
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

## 25. Future improvements

After the hackathon, if sufficient data and time are available:

-   Expand phrase-level DTW to more flexible word/phoneme recognition.
-   Evaluate a custom acoustic model trained from random initialization.
-   Improve speaker robustness and acoustic normalization.
-   Add streaming recognition only after stable offline recognition.
-   Improve local document retrieval and ranking.
-   Add specialist modules only where distinct workflows justify them.
-   Improve recorded-audio composition and prosody.
-   Add stronger audit logging and administrative controls.
-   Evaluate every new feature with a separate test set.

Do not promise these future capabilities as version 1 features.

------------------------------------------------------------------------

## 26. Final engineering principles

1.  **No speech API dependency:** voice input and output use local
    algorithms and team-created recordings, subject to organizer
    approval.
2.  **No pretrained speech models:** no hidden model dependency is
    permitted under the assumed constraint.
3.  **Constrained recognition is described honestly:** MFCC + DTW phrase
    matching is not unrestricted ASR.
4.  **Agents are explicit:** every specialist has a responsibility,
    context, permitted tools and tests.
5.  **The orchestrator coordinates:** it does not bypass security.
6.  **Policies are deterministic:** important college rules are enforced
    in backend code.
7.  **Identity is server-side:** recognized words cannot select another
    user's account.
8.  **Writes require confirmation:** no silent submissions, approvals or
    rejections.
9.  **Ambiguous transactions are reconciled:** never blindly retry a
    possibly successful write.
10. **Answers are grounded:** use actual KIT results or approved
    documents.
11. **Performance is measured:** report real recognition, latency and
    workflow results.
12. **Text fallback is always available.**
13. **A working vertical slice beats an unfinished feature catalogue.**

### Final positioning

**KIT VOX is not an LLM chatbot. It is a custom offline,
constrained-vocabulary voice interface connected to a deterministic
college workflow engine. Its differentiators are team-built speech
processing, custom intent classification, explicit specialist
orchestration, secure tool execution, deterministic policy enforcement
and measurable reliability.**

The implementation must remain aligned with the written hackathon rules
and the actual KIT API contract. Where either is unknown, treat the
feature as unverified rather than assuming it is supported.
