# ============================================================
# ECOLOOP NODE — ECO QUIZZES
# Powered by Next Gen Impact Hub (NGIH)
# ============================================================

import streamlit as st
from datetime import datetime, timezone
from explore_learn import QUIZ_QUESTIONS

NGIH_PILLARS = [
    "Governance & Civic Education",
    "Climate Action & Environment",
    "Business & Entrepreneurship",
    "Technology, Innovation, Media & Arts"
]

DIFFICULTIES = ["Easy", "Medium", "Hard"]

OPTIONS = ["A", "B", "C", "D"]


# ============================================================
# HELPERS
# ============================================================

def _profile_value(profile, key, default=None):
    if isinstance(profile, dict):
        return profile.get(key, default)
    return default


def _is_super_admin(profile):
    return (
        _profile_value(profile, "role", "") == "super_admin"
    )


def _safe_execute(query):
    """
    Supports both Supabase query builders and
    already-executed API responses.
    """
    try:
        execute_method = getattr(query, "execute", None)

        if callable(execute_method):
            response = execute_method()
        else:
            response = query

        return getattr(response, "data", response) or []

    except Exception as error:
        st.error(f"Database operation failed: {error}")
        return None


def _get_quizzes(supabase):
    return _safe_execute(
        supabase.table("quizzes")
        .select("*")
        .eq("is_active", True)
        .order("created_at", desc=True)
    )


def _normalise_difficulty(difficulty):
    value = str(difficulty or "").strip().lower()

    mapping = {
        "easy": "Easy",
        "beginner": "Easy",
        "medium": "Medium",
        "intermediate": "Medium",
        "hard": "Hard",
        "advanced": "Hard"
    }

    return mapping.get(value, "Easy")


def _difficulty_badge(difficulty):
    difficulty = _normalise_difficulty(difficulty)

    colours = {
        "Easy": "🟢",
        "Medium": "🟡",
        "Hard": "🔴"
    }

    return colours.get(difficulty, "⚪")


def _get_member_name(profile):
    return (
        _profile_value(profile, "full_name")
        or "EcoLoop Member"
    )


def _format_date(value):
    if not value:
        return "Not available"

    try:
        return str(value)[:10]
    except Exception:
        return "Not available"


def _clear_active_quiz():
    keys = [
        "eco_active_quiz",
        "eco_quiz_answers",
        "eco_quiz_submitted",
        "eco_quiz_results",
        "eco_quiz_score"
    ]

    for key in keys:
        st.session_state.pop(key, None)


def _normalise_rpc_result(response):
    """
    Supabase RPC results may arrive as a dictionary
    or as a single-item list.
    """
    if isinstance(response, list) and response:
        return response[0]

    return response


def _question_payload_is_valid(questions):
    if not questions:
        return False

    for question in questions:
        required = [
            "question_text",
            "option_a",
            "option_b",
            "option_c",
            "option_d",
            "correct_option",
            "explanation"
        ]

        if not all(
            str(question.get(field, "")).strip()
            for field in required
        ):
            return False

        if question["correct_option"] not in OPTIONS:
            return False

    return True


# ============================================================
# QUIZ CENTRE
# ============================================================

def quiz_centre(supabase, user_id):

    st.subheader("📚 Quiz Centre")

    st.write(
        "Explore environmental and development knowledge "
        "quizzes from across the four NGIH pillars."
    )

    quizzes = _get_quizzes(supabase)

    if quizzes is None:
        return

    if not quizzes:
        st.info("No published quizzes are available yet.")
        return

    col1, col2 = st.columns(2)

    with col1:
        difficulty_filter = st.selectbox(
            "Filter by difficulty",
            ["All"] + DIFFICULTIES,
            key="eco_quiz_difficulty_filter"
        )

    with col2:
        pillar_filter = st.selectbox(
            "Filter by NGIH pillar",
            ["All"] + NGIH_PILLARS,
            key="eco_quiz_pillar_filter"
        )

    filtered = []

    for quiz in quizzes:

        quiz_difficulty = _normalise_difficulty(
            quiz.get("difficulty")
        )

        if (
            difficulty_filter != "All"
            and quiz_difficulty != difficulty_filter
        ):
            continue

        if (
            pillar_filter != "All"
            and quiz.get("category") != pillar_filter
        ):
            continue

        filtered.append(quiz)

    if not filtered:
        st.info("No quizzes match these filters.")
        return

    st.caption(f"{len(filtered)} quiz(es) available")

    for quiz in filtered:

        title = quiz.get("title", "Untitled Quiz")

        difficulty = _normalise_difficulty(
            quiz.get("difficulty")
        )

        with st.container(border=True):

            st.markdown(f"### {title}")

            st.caption(
                f"{_difficulty_badge(difficulty)} "
                f"{difficulty}  |  "
                f"{quiz.get('category', 'General')}"
            )

            st.write(
                quiz.get(
                    "description",
                    "No description available."
                )
            )

            if st.button(
                "Start Quiz",
                key=f"start_quiz_{quiz['id']}",
                use_container_width=True
            ):

                st.session_state["eco_active_quiz"] = quiz
                st.session_state["eco_quiz_answers"] = {}
                st.session_state["eco_quiz_submitted"] = False

                st.rerun()


# ============================================================
# TAKE QUIZ
# ============================================================

def take_quiz(supabase, user_id):

    quiz = st.session_state.get("eco_active_quiz")

    if not quiz:
        return

    st.subheader(
        f"🧠 {quiz.get('title', 'Eco Quiz')}"
    )

    # --------------------------------------------------------
    # LOAD QUESTIONS
    # --------------------------------------------------------

    questions = _safe_execute(
        supabase.table("quiz_questions")
        .select("*")
        .eq("quiz_id", quiz["id"])
        .order("question_order")
    )

    if questions is None:
        return

    if not questions:
        st.warning("This quiz has no questions yet.")
        return

    # --------------------------------------------------------
    # SHOW RESULTS AFTER SUBMISSION
    # --------------------------------------------------------

    if st.session_state.get("eco_quiz_submitted"):

        results = st.session_state.get(
            "eco_quiz_results", []
        )

        score = st.session_state.get(
            "eco_quiz_score", 0
        )

        total = len(results)

        st.success("Quiz completed!")

        st.metric(
            "Your score",
            f"{score} / {total}"
        )

        if total:
            st.progress(score / total)

        percentage = (
            (score / total) * 100
            if total else 0
        )

        st.write(
            f"**Performance:** {percentage:.1f}%"
        )

        st.markdown("### Your results")

        for index, result in enumerate(results, 1):

            if result.get("correct"):
                st.success(f"Question {index}: Correct")
            else:
                st.error(f"Question {index}: Incorrect")

            st.write(result.get("question", ""))

            st.write(
                "Your answer: "
                + str(result.get("selected") or "Not answered")
            )

            st.write(
                "Correct answer: "
                + str(result.get("correct_answer", "Unavailable"))
            )

            st.info(
                result.get("explanation")
                or "No explanation has been provided."
            )

        if st.button(
            "Return to Quiz Centre",
            use_container_width=True
        ):
            _clear_active_quiz()
            st.rerun()

        return

    # --------------------------------------------------------
    # ANSWER FORM
    # --------------------------------------------------------

    st.write(f"**Questions:** {len(questions)}")

    answers = {}

    with st.form("eco_quiz_answer_form"):

        for index, question in enumerate(questions, 1):

            st.markdown(f"**Question {index}**")

            st.write(question["question_text"])

            options = {
                "A": question.get("option_a", ""),
                "B": question.get("option_b", ""),
                "C": question.get("option_c", ""),
                "D": question.get("option_d", "")
            }

            selected = st.radio(
                "Choose your answer:",
                options=list(options.keys()),
                format_func=lambda value, opts=options:
                    f"{value}. {opts[value]}",
                key=f"eco_answer_{question['id']}",
                index=None
            )

            answers[question["id"]] = selected

            st.divider()

        submitted = st.form_submit_button(
            "Submit Quiz",
            use_container_width=True
        )

    # --------------------------------------------------------
    # SECURE SERVER-SIDE MARKING
    # --------------------------------------------------------

    if submitted:

        with st.spinner("Marking your quiz..."):

            try:

                response = supabase.rpc(
                    "grade_eco_quiz",
                    {
                        "p_quiz_id": quiz["id"],
                        "p_answers": answers
                    }
                ).execute()

                data = _normalise_rpc_result(
                    getattr(response, "data", None)
                )

                if not isinstance(data, dict):
                    st.error(
                        "The grading service returned an "
                        "unexpected response."
                    )
                    return

                results = data.get("results", [])
                score = data.get("score", 0)

                if not results:
                    st.error("No quiz results were returned.")
                    return

                st.session_state["eco_quiz_results"] = results
                st.session_state["eco_quiz_score"] = score
                st.session_state["eco_quiz_submitted"] = True

                st.rerun()

            except Exception as error:
                st.error(
                    f"Could not submit quiz: {error}"
                )


# ============================================================
# CREATE QUIZ
# ============================================================

def create_quiz(supabase, user_id):

    st.subheader("✍️ Create a Quiz")

    st.write(
        "Create a knowledge quiz and submit it "
        "for Super Admin review."
    )

    question_count = st.number_input(
        "Number of questions",
        min_value=1,
        max_value=30,
        value=5,
        step=1,
        key="eco_new_question_count"
    )

    questions = []

    with st.form("eco_create_quiz_form"):

        title = st.text_input("Quiz title")

        description = st.text_area(
            "Quiz description"
        )

        category = st.selectbox(
            "NGIH pillar",
            NGIH_PILLARS
        )

        difficulty = st.selectbox(
            "Difficulty",
            DIFFICULTIES
        )

        for index in range(int(question_count)):

            st.markdown(f"#### Question {index + 1}")

            question_text = st.text_input(
                "Question",
                key=f"create_question_{index}"
            )

            option_a = st.text_input(
                "Option A",
                key=f"create_a_{index}"
            )

            option_b = st.text_input(
                "Option B",
                key=f"create_b_{index}"
            )

            option_c = st.text_input(
                "Option C",
                key=f"create_c_{index}"
            )

            option_d = st.text_input(
                "Option D",
                key=f"create_d_{index}"
            )

            correct_option = st.selectbox(
                "Correct answer",
                OPTIONS,
                key=f"create_correct_{index}"
            )

            explanation = st.text_area(
                "Explain why this answer is correct",
                key=f"create_explanation_{index}"
            )

            questions.append({
                "question_text": question_text.strip(),
                "option_a": option_a.strip(),
                "option_b": option_b.strip(),
                "option_c": option_c.strip(),
                "option_d": option_d.strip(),
                "correct_option": correct_option,
                "explanation": explanation.strip(),
                "question_order": index + 1,
                "points": 1
            })

        submitted = st.form_submit_button(
            "Submit Quiz for Review",
            use_container_width=True
        )

    if submitted:

        if not title.strip():
            st.error("Enter a quiz title.")
            return

        if not description.strip():
            st.error("Enter a quiz description.")
            return

        if not _question_payload_is_valid(questions):
            st.error(
                "Please complete every question, all four options, "
                "the correct answer and its explanation."
            )
            return

        submission_data = {
            "user_id": user_id,
            "title": title.strip(),
            "description": description.strip(),
            "category": category,
            "difficulty": difficulty,
            "questions": questions,
            "status": "pending"
        }

        result = _safe_execute(
            supabase.table("quiz_submissions")
            .insert(submission_data)
        )

        if result is not None:
            st.success(
                "Your quiz has been submitted for "
                "Super Admin review!"
            )
            st.rerun()


# ============================================================
# MY QUIZ SUBMISSIONS
# ============================================================

def my_submissions(supabase, user_id):

    st.subheader("📋 My Quiz Submissions")

    submissions = _safe_execute(
        supabase.table("quiz_submissions")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
    )

    if submissions is None:
        return

    if not submissions:
        st.info("You haven't submitted any quizzes yet.")
        return

    edit_id = st.session_state.get(
        "eco_edit_submission_id"
    )

    for submission in submissions:

        submission_id = submission["id"]

        status = submission.get(
            "status", "pending"
        )

        with st.container(border=True):

            st.markdown(
                f"### {submission.get('title', 'Untitled Quiz')}"
            )

            st.write(f"**Status:** {status.title()}")

            st.caption(
                f"{submission.get('category', '')} | "
                f"{submission.get('difficulty', '')}"
            )

            st.caption(
                f"Submitted: {_format_date(submission.get('created_at'))}"
            )

            feedback = submission.get("admin_feedback")

            if feedback:
                st.info(f"Admin feedback: {feedback}")

            if status == "pending":
                st.info("Your quiz is awaiting review.")

            elif status == "approved":
                st.success(
                    "Your quiz has been approved."
                )

            elif status == "published":
                st.success(
                    "Your quiz is published in Quiz Centre."
                )

            elif status == "rejected":

                st.warning(
                    "Your quiz needs changes before it can "
                    "be reviewed again."
                )

                if st.button(
                    "Edit and Resubmit",
                    key=f"edit_submission_{submission_id}",
                    use_container_width=True
                ):
                    st.session_state[
                        "eco_edit_submission_id"
                    ] = submission_id

                    st.rerun()

    # --------------------------------------------------------
    # EDIT SELECTED SUBMISSION
    # --------------------------------------------------------

    if edit_id:

        submission = next(
            (
                item for item in submissions
                if item["id"] == edit_id
            ),
            None
        )

        if submission and submission.get("status") in [
            "pending",
            "rejected"
        ]:

            st.divider()
            st.subheader("✏️ Edit Your Quiz")

            existing_questions = submission.get(
                "questions", []
            )

            if not isinstance(existing_questions, list):
                existing_questions = []

            existing_count = max(
                1, len(existing_questions)
            )

            edit_question_count = st.number_input(
                "Number of questions",
                min_value=1,
                max_value=30,
                value=existing_count,
                step=1,
                key=f"edit_count_{edit_id}"
            )

            updated_questions = []

            with st.form(f"edit_quiz_form_{edit_id}"):

                title = st.text_input(
                    "Quiz title",
                    value=submission.get("title", "")
                )

                description = st.text_area(
                    "Quiz description",
                    value=submission.get("description", "")
                )

                current_category = submission.get(
                    "category", NGIH_PILLARS[0]
                )

                category_index = (
                    NGIH_PILLARS.index(current_category)
                    if current_category in NGIH_PILLARS
                    else 0
                )

                category = st.selectbox(
                    "NGIH pillar",
                    NGIH_PILLARS,
                    index=category_index
                )

                current_difficulty = _normalise_difficulty(
                    submission.get("difficulty")
                )

                difficulty_index = DIFFICULTIES.index(
                    current_difficulty
                )

                difficulty = st.selectbox(
                    "Difficulty",
                    DIFFICULTIES,
                    index=difficulty_index
                )

                for index in range(int(edit_question_count)):

                    old = (
                        existing_questions[index]
                        if index < len(existing_questions)
                        else {}
                    )

                    st.markdown(f"#### Question {index + 1}")

                    question_text = st.text_input(
                        "Question",
                        value=old.get("question_text", ""),
                        key=f"edit_q_{edit_id}_{index}"
                    )

                    option_a = st.text_input(
                        "Option A",
                        value=old.get("option_a", ""),
                        key=f"edit_a_{edit_id}_{index}"
                    )

                    option_b = st.text_input(
                        "Option B",
                        value=old.get("option_b", ""),
                        key=f"edit_b_{edit_id}_{index}"
                    )

                    option_c = st.text_input(
                        "Option C",
                        value=old.get("option_c", ""),
                        key=f"edit_c_{edit_id}_{index}"
                    )

                    option_d = st.text_input(
                        "Option D",
                        value=old.get("option_d", ""),
                        key=f"edit_d_{edit_id}_{index}"
                    )

                    old_correct = old.get(
                        "correct_option", "A"
                    )

                    correct_index = (
                        OPTIONS.index(old_correct)
                        if old_correct in OPTIONS
                        else 0
                    )

                    correct_option = st.selectbox(
                        "Correct answer",
                        OPTIONS,
                        index=correct_index,
                        key=f"edit_correct_{edit_id}_{index}"
                    )

                    explanation = st.text_area(
                        "Explanation",
                        value=old.get("explanation", ""),
                        key=f"edit_explanation_{edit_id}_{index}"
                    )

                    updated_questions.append({
                        "question_text": question_text.strip(),
                        "option_a": option_a.strip(),
                        "option_b": option_b.strip(),
                        "option_c": option_c.strip(),
                        "option_d": option_d.strip(),
                        "correct_option": correct_option,
                        "explanation": explanation.strip(),
                        "question_order": index + 1,
                        "points": 1
                    })

                save_changes = st.form_submit_button(
                    "Save Changes and Resubmit",
                    use_container_width=True
                )

            if save_changes:

                if not title.strip() or not description.strip():
                    st.error(
                        "Enter a title and description."
                    )
                    return

                if not _question_payload_is_valid(
                    updated_questions
                ):
                    st.error(
                        "Complete every question, option "
                        "and explanation before resubmitting."
                    )
                    return

                update_data = {
                    "title": title.strip(),
                    "description": description.strip(),
                    "category": category,
                    "difficulty": difficulty,
                    "questions": updated_questions,
                    "status": "pending",
                    "admin_feedback": None,
                    "reviewed_by": None,
                    "reviewed_at": None,
                    "updated_at": datetime.now(
                        timezone.utc
                    ).isoformat()
                }

                result = _safe_execute(
                    supabase.table("quiz_submissions")
                    .update(update_data)
                    .eq("id", edit_id)
                    .eq("user_id", user_id)
                )

                if result is not None:
                    st.session_state.pop(
                        "eco_edit_submission_id", None
                    )

                    st.success(
                        "Your updated quiz has been resubmitted."
                    )

                    st.rerun()

            if st.button(
                "Cancel Editing",
                key=f"cancel_edit_{edit_id}"
            ):
                st.session_state.pop(
                    "eco_edit_submission_id", None
                )
                st.rerun()


# ============================================================
# SUPER ADMIN REVIEW
# ============================================================

def admin_review(supabase, user_id):

    st.subheader("🛡️ Super Admin — Quiz Review")

    submissions = _safe_execute(
        supabase.table("quiz_submissions")
        .select("*")
        .eq("status", "pending")
        .order("created_at")
    )

    if submissions is None:
        return

    if not submissions:
        st.success(
            "There are no pending quiz submissions."
        )
        return

    st.caption(
        f"{len(submissions)} submission(s) awaiting review"
    )

    for submission in submissions:

        submission_id = submission["id"]

        with st.container(border=True):

            st.markdown(
                f"### {submission.get('title', 'Untitled Quiz')}"
            )

            st.write(
                submission.get("description", "")
            )

            st.caption(
                f"{submission.get('category', '')} | "
                f"{submission.get('difficulty', '')}"
            )

            st.caption(
                f"Submitted: {_format_date(submission.get('created_at'))}"
            )

            questions = submission.get("questions", [])

            st.write(
                f"**Number of questions:** {len(questions)}"
            )

            with st.expander("Review quiz questions"):

                for index, question in enumerate(
                    questions, 1
                ):

                    st.markdown(
                        f"**Question {index}:** "
                        f"{question.get('question_text', '')}"
                    )

                    st.write(
                        f"A. {question.get('option_a', '')}"
                    )
                    st.write(
                        f"B. {question.get('option_b', '')}"
                    )
                    st.write(
                        f"C. {question.get('option_c', '')}"
                    )
                    st.write(
                        f"D. {question.get('option_d', '')}"
                    )

                    st.write(
                        "**Correct answer:** "
                        + str(question.get("correct_option", ""))
                    )

                    st.info(
                        question.get("explanation", "")
                    )

            notes = st.text_area(
                "Review feedback",
                key=f"review_notes_{submission_id}",
                placeholder="Explain any changes needed if rejecting..."
            )

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    "Approve and Publish",
                    key=f"approve_{submission_id}",
                    use_container_width=True
                ):

                    try:

                        response = supabase.rpc(
                            "publish_quiz_submission",
                            {
                                "p_submission_id": submission_id
                            }
                        ).execute()

                        st.success(
                            "Quiz approved and published successfully!"
                        )

                        st.rerun()

                    except Exception as error:
                        st.error(
                            f"Publishing failed: {error}"
                        )

            with col2:

                if st.button(
                    "Reject Submission",
                    key=f"reject_{submission_id}",
                    use_container_width=True
                ):

                    if not notes.strip():
                        st.warning(
                            "Please provide feedback explaining "
                            "why this quiz is being rejected."
                        )

                    else:

                        result = _safe_execute(
                            supabase.table("quiz_submissions")
                            .update({
                                "status": "rejected",
                                "admin_feedback": notes.strip(),
                                "reviewed_by": user_id,
                                "reviewed_at": datetime.now(
                                    timezone.utc
                                ).isoformat(),
                                "updated_at": datetime.now(
                                    timezone.utc
                                ).isoformat()
                            })
                            .eq("id", submission_id)
                        )

                        if result is not None:
                            st.success(
                                "Submission rejected. "
                                "The member can now edit and resubmit."
                            )
                            st.rerun()

# ============================================================
# IMPORT ORIGINAL NGIH QUIZ BANK
# ============================================================

from explore_learn import QUIZ_QUESTIONS


def seed_original_eco_quizzes(supabase):
    pillars = [
        "Climate Action & Environment",
        "Governance & Civic Education",
        "Business & Entrepreneurship",
        "Technology, Innovation, Media & Arts",
    ]

    letters = ["A", "B", "C", "D"]
    imported = 0
    skipped = 0

    for pillar in pillars:
        bank = [
            q for q in QUIZ_QUESTIONS
            if q.get("category") == pillar
        ]

        if not bank:
            continue

        title = f"NGIH Original 50 — {pillar}"

        existing = _safe_execute(
            supabase.table("quizzes")
            .select("id")
            .eq("title", title)
        )

        if existing is None:
            return imported, skipped, "Could not check existing quizzes."

        if existing:
            skipped += 1
            continue

        quiz_result = supabase.table("quizzes").insert({
            "title": title,
            "description": (
                f"Original NGIH quiz collection covering "
                f"{pillar}. Includes {len(bank)} questions."
            ),
            "category": pillar,
            "difficulty": "Mixed",
            "is_active": True,
        }).execute()

        quiz_data = _normalise_rpc_result(quiz_result.data)

        if isinstance(quiz_data, dict):
            quiz_data = [quiz_data]

        if not quiz_data:
            return imported, skipped, f"Could not create {pillar} quiz."

        quiz_id = quiz_data[0]["id"]

        question_rows = []
        answer_rows = []

        for order, item in enumerate(bank, start=1):
            question_id = str(__import__("uuid").uuid4())

            question_rows.append({
                "id": question_id,
                "quiz_id": quiz_id,
                "question_text": item["question"],
                "option_a": item["options"][0],
                "option_b": item["options"][1],
                "option_c": item["options"][2],
                "option_d": item["options"][3],
                "question_order": order,
                "points": 1,
            })

            answer_rows.append({
                "question_id": question_id,
                "correct_option": letters[item["answer"]],
                "explanation": item["explanation"],
            })

        supabase.table("quiz_questions").insert(
            question_rows
        ).execute()

        supabase.table("quiz_answer_keys").insert(
            answer_rows
        ).execute()

        imported += len(bank)

    return imported, skipped, None
    
# ============================================================
# MAIN ECO QUIZZES PAGE
# ============================================================

def render_eco_quizzes(supabase, user_id, profile=None):

    st.title("🧠 Eco Quizzes")

    st.write(
        "Learn, test your knowledge, challenge yourself "
        "and contribute to environmental awareness."
    )

    if not user_id:
        st.warning(
            "Please log in to access Eco Quizzes."
        )
        return

    is_admin = _is_super_admin(profile)

    # IMPORT ORIGINAL NGIH QUIZZES
    if is_admin:
        with st.expander("⚙️ Original NGIH Quiz Bank"):
            st.write(
                "Load the original 50 questions into the "
                "four NGIH pillar quiz collections."
            )

            if st.button(
                "Import Original 50 Quizzes",
                key="import_original_50_quizzes",
                use_container_width=True
            ):
                with st.spinner("Importing original quizzes..."):
                    imported, skipped, error = (
                        seed_original_eco_quizzes(supabase)
                    )

                if error:
                    st.error(error)
                else:
                    st.success(
                        f"Imported {imported} questions. "
                        f"Skipped {skipped} existing collections."
                    )
                    st.rerun()

    # --------------------------------------------------------
    # ACTIVE QUIZ
    # --------------------------------------------------------

    if st.session_state.get("eco_active_quiz"):

        if st.button("← Back to Eco Quizzes"):
            _clear_active_quiz()
            st.rerun()

        take_quiz(supabase, user_id)
        return

    # --------------------------------------------------------
    # PAGE SECTIONS
    # --------------------------------------------------------

    tab_names = [
        "Quiz Centre",
        "Create a Quiz",
        "My Submissions"
    ]

    if is_admin:
        tab_names.append("Admin Review")

    tabs = st.tabs(tab_names)

    with tabs[0]:
        quiz_centre(supabase, user_id)

    with tabs[1]:
        create_quiz(supabase, user_id)

    with tabs[2]:
        my_submissions(supabase, user_id)

    if is_admin:
        with tabs[3]:
            admin_review(supabase, user_id)


# ============================================================
# END OF ECO QUIZZES
# ============================================================
