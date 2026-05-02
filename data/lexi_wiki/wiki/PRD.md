# Lexi — AI-Powered Language Adventure Bot

## Project overview:

The goal of this project is to develop an AI-powered bot for interactive storytelling for the purpose of teaching kids foreign language. A child chooses a language they're learning, a main character, and a setting. The bot, powered by an LLM, starts telling a story. After each paragraph, it presents the child with two choices on how to continue the adventure. Once every few times the bot presents child with small quiz about vocabulary used in story. At the end, the bot generates a unique cover image for their story.

### 1. Vision & Mission (The "Why")

To make learning a new language an unforgettable adventure for children. Lexi transforms passive vocabulary drills into an active, creative storytelling experience where the child is the hero of their own tale. Our mission is to foster a love for language through imagination and play.

### 2. Core User Experience (The "What")

A child opens Lexi and is guided through a simple setup:

1. **Choose Your Adventure:** They select their native language (e.g., Spanish) and the language they want to practice (e.g., English), define their main character (e.g., "a clever fox"), and pick a setting (e.g., "a futuristic city made of glass").
2. **The Story Begins:** Our LLM-powered Storyteller crafts the opening paragraph of a unique story based on the child's choices.
3. **Drive the Narrative:** After each story segment (1-2 paragraphs), the child is presented with two distinct choices on how to proceed (e.g., "Explore the tall tower" or "Follow the mysterious robot").
4. **Learn as You Go:** Throughout the story, key vocabulary words are highlighted and presented as buttons under a block of text. Tapping a word instantly brings up a simple definition and a translation in their native language.
5. **Check Your Knowledge:** Periodically (e.g., after every 5 choices), a mini-quiz appears. For project's MVP it's always question where kid should choose correct translation for a word or group of words used in one of previous story bites. Later more complex quizes can be added with questions that better reveal general understanding (like "what X said to Y?" with choices), or multiple choice questions where you need to select all true statements about story so far.
6. **Your Unique Masterpiece:** The story concludes when a token threshold is met or the LLM generates a natural ending. Upon completion, the bot sends a "Generating your cover..." message and triggers an asynchronous job. The job sends the final image to the user. This image can be saved and shared.

### 3. Key Features & Requirements (The "How")

#### 3.1. Story Initiation & Setup

- Inputs:

  - Native Language: determined by bot as default Telegram language of user.
  - Target Language: fuzzy text comparison of user input and list of supported languages. Accept also country flag emojis.
  - Protagonist: User-defined text input (with content moderation).
  - Setting: User-defined text input (with content moderation).
  - Content Moderation: All user-defined text inputs (protagonist, setting) **must** be passed through the OpenAI Moderation API before being used in prompts. If content is flagged, the bot will politely ask the user to try a different idea.

- UI: For MVP - clean and simple, enough to get the job done: inline buttons for adventure choices and quizzes, pop-ups for word translation.

#### 3.2. Interactive Narrative Engine

- Core Logic: An LLM generates story segments based on user choices. The prompt engineering will need to maintain narrative consistency, age-appropriate tone, and educational value.
  Pacing: The story unfolds in turns. Each turn consists of a story segment from the bot followed by two actionable choices for the user.

  - Prompt Management: Prompts will be stored in a separate prompts.py module for easy management.
  - Initial Story Prompt Template:

  ```
    You are Lexi, a fun and encouraging AI storyteller for a child learning {target_language}.
    Their native language is {native_language}.
    The story is about a {protagonist} in a {setting}.
    The tone should be {tone_adjective_1}, {tone_adjective_2}, and suitable for a 10-year-old.
    Write the first paragraph of the story in {target_language}.
    Keep the story text under 75 words.
    After the story text, on a new line, provide two choices for the user to continue the story, formatted as a numbered list. Example:
    1. Choice one...
    2. Choice two...
  ```

- Key Word Highlighting:
  - Requirement: The system will identify 1-2 suitable vocabulary words in the story text. In the Telegram message, these words will be **bolded**. The message will have an InlineKeyboard with buttons corresponding to the bolded words.
  * Requirement: The logic for key words selection should be isolated because it can be subject to change. For MVP it will be random word from the story bit longer than certain threshold.
  * Requirement: each story bit has 1-2 key words.
  * Requirement: key words cannot repeat in the same story unless user failed quiz for that word.
  * Possible options for choosing key words in the future: 1) based on precomputed frequency of word in some large text corpus; 2) based on previous mistakes of that user in quiz; 3) based on importance in story bit; 4) group of words can be selected (e.g., phrasal verbs)
- Vocabulary helper
  - Trigger: User presses an _InlineKeyboardButton_ with the vocabulary word.
  - Action: The bot will call _answer_callback_query_ with the _show_alert_ flag set to True. The alert will contain a simple definition and a translation, generated by an LLM call. The result of this LLM call **must** be cached in Redis.

#### 3.4. Comprehension Quizzes

- Frequency: Triggered periodically. We can start with a fixed trigger (e.g., every 5 story turns) and explore dynamic triggers later.
- Format: Simple multiple-choice questions. (e.g., "¿Qué significa la palabra 'brave'?" A. Asustada, B. Fuerte y sin miedo, C. Elegante").
- Content: Half of the words highlighted since last quiz (chosen at random).

#### 3.5. Story Completion & Reward (The "Book Cover" Generator)

- Trigger:
  - a) The user reaches a narrative conclusion (i.e. LLM considers story finished), or
  - b) The conversation history in the Redis session key exceeds 3000 tokens. The system prompt will then be updated to:
  ```
  Please conclude the story in a satisfying way in the next 1-2 paragraphs
  ```
- Core Logic:
  - The system sends a summary of the story's key elements (character, setting, major plot points) to an image generation model (DALL-E).
  - The prompt will be engineered to request a "storybook cover" or "illustration" style.
- Output: A unique, shareable image that serves as a trophy for finishing the story.
- Image generation prompt template:
  ```
  Create a vibrant, colorful children's storybook cover illustration.
  The style should be friendly and magical.
  The scene should feature: a {protagonist}.
  The setting is: {setting}.
  Key story events included: {summary_of_choices}.
  Do not include any text or words in the image.
  ```

### 4. Target Audience

- Primary: Children aged 7-12 who are beginning to learn a foreign language, either at school or at home.
- Secondary: Parents and educators looking for engaging, screen-time-positive educational tools.

## System Architecture

- **Web Server:** FastAPI serves as the webhook endpoint for Telegram.
- **Bot Logic:** aiogram is used within the FastAPI app to parse Telegram Update objects and route them to handlers.
- **Async Tasks:** Celery with a Redis broker handles all slow operations (LLM calls, image generation) to keep the bot responsive.
- **Session Store:** Redis is used to store the conversation history for each active story.
- **Persistent Storage:** PostgreSQL stores final data about users, completed stories, and vocabulary progress.

## Data Schema (PostgreSQL)

- **Table** `users`:

  - `id` (BIGINT, Primary Key) - Telegram User ID
  - `native_language_code` (VARCHAR(10))
  - `created_at` (TIMESTAMP)

- **Table** `stories`:

  - `id` (SERIAL, Primary Key)
  - `user_id` (BIGINT, Foreign Key to users.id)
  - `target_language_code` (VARCHAR(10))
  - `protagonist` (TEXT)
  - `setting` (TEXT)
  - `full_story_text` (TEXT) - The final concatenated story
  - `cover_image_url` (TEXT) - URL of the generated DALL-E image
  - `started_at` (TIMESTAMP)
  - `finished_at` (TIMESTAMP, NULLable)

- **Table** `user_vocabulary_progress`:

  - `id` (SERIAL, Primary Key)
  - `user_id` (BIGINT, Foreign Key to users.id)
  - `word` (TEXT)
  - `language_code` (VARCHAR(10))
  - `times_seen` (INTEGER)
  - `times_quized` (INTEGER NULLable)
  - `correct_answers` (INTEGER NULLable)
  - `last_seen_at` (TIMESTAMP)

  Constraint: UNIQUE on (user_id, language_code, word)

## Technical Stack

- Python 3.12
- FastAPI (for web serving)
- aiogram (for Telegram API interaction)
- PostgreSQL with asyncpg (for storage)
- SQLModel (for ORM)
- Celery (for async tasks)
- Redis (for Celery broker and caching)
- httpx (for making async API calls to OpenAI)
- thefuzz (for language selection)
- Pydantic and .env (for configuration)
- OpenAI API (GPT-4o for story/text, DALL-E 3 for images)
