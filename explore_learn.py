
# ============================================================
# ECOLOOP NODE — EXPLORE & LEARN
# Powered by Next Gen Impact Hub (NGIH)
# ============================================================

import streamlit as st
import pandas as pd
import uuid
from datetime import datetime


# ============================================================
# 1. LEARNING CONTENT
# ============================================================

LESSONS = [
    {
        "id": "eco_001",
        "title": "Where does our waste go?",
        "category": "Climate Action & Environment",
        "pillar": "Environment",
        "minutes": 3,
        "description": "Understand what happens when waste is not properly managed.",
        "content": [
            ("The problem",
             "Waste does not simply disappear when we throw it away. "
             "Poorly managed waste can end up in streets, drainage systems, "
             "rivers and open spaces."),
            ("Why it matters",
             "Blocked drains can contribute to flooding. Plastic pollution "
             "can harm wildlife, while unmanaged waste affects the cleanliness "
             "and wellbeing of communities."),
            ("What can we do?",
             "Separate recyclable materials, use appropriate collection points "
             "and encourage responsible disposal in your community."),
            ("Think about it",
             "What happens to the waste produced at your school, home or workplace?")
        ],
        "action": "Identify one waste-management problem in your community."
    },
    {
        "id": "eco_002",
        "title": "Can waste become wealth?",
        "category": "Business & Entrepreneurship",
        "pillar": "Entrepreneurship",
        "minutes": 3,
        "description": "Discover how recycling can create opportunities and jobs.",
        "content": [
            ("Waste as a resource",
             "Some materials we throw away can be collected, sorted, reused "
             "or recycled instead of being discarded."),
            ("The business opportunity",
             "Young entrepreneurs can explore collection services, recycling, "
             "repair, upcycling and products made from recovered materials."),
            ("The community benefit",
             "Green businesses can create employment, reduce pollution and "
             "support local economic development."),
            ("Think about it",
             "What useful product or service could be created from waste in your area?")
        ],
        "action": "Think of one small environmental business idea."
    },
    {
        "id": "eco_003",
        "title": "Who is responsible for a clean community?",
        "category": "Governance & Civic Education",
        "pillar": "Governance",
        "minutes": 3,
        "description": "Explore citizenship, environmental responsibility and leadership.",
        "content": [
            ("Shared responsibility",
             "A clean and healthy environment requires participation from "
             "individuals, communities, businesses and public institutions."),
            ("The role of citizens",
             "People can report waste problems, participate in community "
             "clean-ups and ask questions about local environmental services."),
            ("The role of leadership",
             "Responsible leadership involves listening to communities, "
             "planning services and being accountable for decisions."),
            ("Think about it",
             "How can young people influence environmental decisions in their communities?")
        ],
        "action": "Identify one environmental issue that deserves community attention."
    },
    {
        "id": "eco_004",
        "title": "Technology for a greener future",
        "category": "Technology, Innovation, Media & Arts",
        "pillar": "Innovation",
        "minutes": 3,
        "description": "Discover how innovation can improve environmental protection.",
        "content": [
            ("Technology and the environment",
             "Technology can help communities monitor waste, organise collections, "
             "share information and understand environmental problems."),
            ("Young innovators",
             "Young people can use digital tools, creative media and simple "
             "inventions to develop solutions to local environmental challenges."),
            ("Responsible innovation",
             "Good technology should solve real problems, respect people's "
             "privacy and be accessible to the communities using it."),
            ("Think about it",
             "What technology could make waste collection easier in your area?")
        ],
        "action": "Suggest one digital or technological solution to a waste problem."
    },
    {
        "id": "eco_005",
        "title": "Climate change starts with understanding",
        "category": "Climate Action & Environment",
        "pillar": "Environment",
        "minutes": 4,
        "description": "Learn how climate change affects communities and livelihoods.",
        "content": [
            ("What is climate change?",
             "Climate change refers to long-term changes in temperatures "
             "and weather patterns. Human activities, particularly burning "
             "fossil fuels, are the main driver of recent global warming."),
            ("Why should communities care?",
             "Changes in rainfall, rising temperatures and extreme weather "
             "can affect agriculture, water availability, health and livelihoods."),
            ("The connection to waste",
             "Reducing waste, reusing materials and improving resource management "
             "can support broader environmental sustainability."),
            ("Think about it",
             "How might changing rainfall patterns affect families and farmers in Zimbabwe?")
        ],
        "action": "Identify one climate-related challenge affecting your community."
    }
]


QUIZ_QUESTIONS = [
    {
        "question": "What can happen when waste blocks drainage systems?",
        "options": [
            "It can contribute to flooding",
            "It improves water quality",
            "It creates more drainage space",
            "It makes waste disappear"
        ],
        "answer": 0,
        "explanation": "Blocked drainage systems can prevent water from flowing properly."
    },
    {
        "question": "Which of these is an example of a green business?",
        "options": [
            "Illegal dumping",
            "A business collecting recyclable materials",
            "Burning waste in open spaces",
            "Throwing reusable materials away"
        ],
        "answer": 1,
        "explanation": "Collecting recyclable materials can create economic value while reducing waste."
    },
    {
        "question": "Who has a role in keeping communities clean?",
        "options": [
            "Only government",
            "Only schools",
            "Only waste collectors",
            "Individuals, communities, businesses and public institutions"
        ],
        "answer": 3,
        "explanation": "Environmental responsibility is shared across society."
    },
    {
        "question": "How can technology support environmental protection?",
        "options": [
            "By helping monitor and organise waste collection",
            "By encouraging illegal dumping",
            "By preventing communities from sharing information",
            "By making recycling impossible"
        ],
        "answer": 0,
        "explanation": "Digital tools can support reporting, monitoring and coordination."
    },
    {
        "question": "What is the main driver of recent global warming?",
        "options": [
            "Recycling paper",
            "Planting trees",
            "Human activities, especially fossil fuel use",
            "Separating household waste"
        ],
        "answer": 2,
        "explanation": "Human activities, especially greenhouse gas emissions from fossil fuels, are the main driver."
    }
]


# ============================================================
# 2. HELPER FUNCTIONS
# ============================================================

def _safe_name(name):
    return name or "EcoLoop Member"


def _load_comments(supabase, content_type, content_id):
    try:
        response = (
            supabase.table("learning_comments")
            .select("*")
            .eq("content_type", content_type)
            .eq("content_id", str(content_id))
            .order("created_at", desc=False)
            .execute()
        )
        return response.data or []
    except Exception as e:
        st.warning(f"Comments are temporarily unavailable: {e}")
        return []


def _comments_section(supabase, user_id, content_type, content_id, user_name):
    st.markdown("#### 💬 Community discussion")

    comments = _load_comments(supabase, content_type, content_id)

    if comments:
        for comment in comments:
            with st.container(border=True):
                st.markdown(
                    f"**{_safe_name(comment.get('full_name'))}**"
                )
                st.write(comment.get("comment", ""))
                st.caption(comment.get("created_at", ""))
    else:
        st.caption("No comments yet. Start the conversation!")

    comment_text = st.text_area(
        "Share your thoughts",
        key=f"comment_{content_type}_{content_id}",
        max_chars=1000,
        placeholder="Share an idea, ask a question or contribute knowledge..."
    )

    if st.button(
        "Post comment",
        key=f"post_{content_type}_{content_id}",
        use_container_width=True
    ):
        if not user_id:
            st.error("Please sign in to comment.")
        elif not comment_text.strip():
            st.warning("Please write a comment first.")
        else:
            try:
                supabase.table("learning_comments").insert({
                    "user_id": user_id,
                    "full_name": user_name,
                    "content_type": content_type,
                    "content_id": str(content_id),
                    "comment": comment_text.strip()
                }).execute()

                st.success("Your comment has been shared!")
                st.rerun()

            except Exception as e:
                st.error(f"Could not post your comment: {e}")


# ============================================================
# 3. READING LIBRARY
# ============================================================

def _reading_library(supabase, user_id, group_id, user_name):

    st.subheader("📚 Discover & Learn")
    st.write("Short lessons connecting knowledge to real community action.")

    categories = [
        "All categories",
        "Climate Action & Environment",
        "Governance & Civic Education",
        "Business & Entrepreneurship",
        "Technology, Innovation, Media & Arts"
    ]

    selected_category = st.selectbox(
        "Explore a learning area",
        categories,
        key="learning_category"
    )

    lessons = LESSONS

    if selected_category != "All categories":
        lessons = [
            lesson for lesson in LESSONS
            if lesson["category"] == selected_category
        ]

    for lesson in lessons:
        with st.container(border=True):
            st.markdown(f"### {lesson['title']}")
            st.caption(
                f"{lesson['category']} • "
                f"{lesson['minutes']} minute read"
            )
            st.write(lesson["description"])

            if st.button(
                "Read lesson",
                key=f"read_{lesson['id']}",
                use_container_width=True
            ):
                st.session_state["selected_learning_lesson"] = lesson["id"]
                st.rerun()

    selected_id = st.session_state.get("selected_learning_lesson")

    if selected_id:
        lesson = next(
            (item for item in LESSONS if item["id"] == selected_id),
            None
        )

        if lesson:
            st.divider()
            st.markdown(f"## {lesson['title']}")
            st.caption(
                f"{lesson['category']} • "
                f"{lesson['minutes']} minute read"
            )

            for heading, paragraph in lesson["content"]:
                st.markdown(f"### {heading}")
                st.write(paragraph)

            st.info(f"🌱 **Your action:** {lesson['action']}")

            if st.button(
                "✅ Mark lesson as completed",
                key=f"complete_{lesson['id']}",
                use_container_width=True
            ):
                if not user_id:
                    st.error("Please sign in to record your progress.")
                else:
                    try:
                        supabase.table("learning_completions").insert({
                            "user_id": user_id,
                            "group_id": group_id,
                            "lesson_id": lesson["id"]
                        }).execute()

                        st.success(
                            "Lesson completed! Your learning points "
                            "have been recorded."
                        )

                    except Exception as e:
                        error_text = str(e).lower()

                        if "duplicate" in error_text or "unique" in error_text:
                            st.info("You have already completed this lesson.")
                        else:
                            st.error(f"Could not record completion: {e}")

            st.divider()

            _comments_section(
                supabase,
                user_id,
                "lesson",
                lesson["id"],
                user_name
            )

            if st.button("← Back to lessons", key="back_lessons"):
                st.session_state.pop("selected_learning_lesson", None)
                st.rerun()


# ============================================================
# 4. QUIZ CENTRE
# ============================================================

def _quiz_centre(supabase, user_id, group_id):

    st.subheader("🧠 Knowledge Challenge")
    st.write("Test what you know about the environment and sustainable communities.")

    if "explore_quiz_answers" not in st.session_state:
        st.session_state["explore_quiz_answers"] = {}

    if "explore_quiz_submitted" not in st.session_state:
        st.session_state["explore_quiz_submitted"] = False

    answers = st.session_state["explore_quiz_answers"]

    for index, question in enumerate(QUIZ_QUESTIONS):
        st.markdown(f"**Question {index + 1} of {len(QUIZ_QUESTIONS)}**")
        st.write(question["question"])

        selected = st.radio(
            "Choose your answer:",
            question["options"],
            index=None,
            key=f"explore_answer_{index}",
            disabled=st.session_state["explore_quiz_submitted"],
            label_visibility="collapsed"
        )

        if selected is not None:
            answers[index] = question["options"].index(selected)

        if st.session_state["explore_quiz_submitted"]:
            correct = question["answer"]
            if answers.get(index) == correct:
                st.success("Correct! " + question["explanation"])
            else:
                st.error(
                    "Not quite. " +
                    question["explanation"]
                )

        st.divider()

    if not st.session_state["explore_quiz_submitted"]:

        if st.button("Submit my answers", use_container_width=True):

            if len(answers) != len(QUIZ_QUESTIONS):
                st.warning("Please answer all questions first.")
            else:
                score = sum(
                    1 for index, question in enumerate(QUIZ_QUESTIONS)
                    if answers.get(index) == question["answer"]
                )

                st.session_state["explore_quiz_score"] = score
                st.session_state["explore_quiz_submitted"] = True
                st.rerun()

    else:
        score = st.session_state.get("explore_quiz_score", 0)

        st.markdown("### Your results")
        st.metric(
            "Your score",
            f"{score} / {len(QUIZ_QUESTIONS)}"
        )

        if score == len(QUIZ_QUESTIONS):
            st.success("Outstanding! You got every question right.")
        elif score >= 3:
            st.success("Good work! Keep building your knowledge.")
        else:
            st.info("Keep learning. You can try again!")

        if st.button("Try the quiz again", use_container_width=True):
            st.session_state["explore_quiz_answers"] = {}
            st.session_state["explore_quiz_submitted"] = False
            st.session_state.pop("explore_quiz_score", None)
            st.rerun()

        st.caption(
            "Quiz points will be connected to the universal points "
            "ledger as part of the database setup."
        )


# ============================================================
# 5. RESOURCE LIBRARY AND MEMBER UPLOADS
# ============================================================

def _resource_library(supabase, user_id, is_coordinator):

    st.subheader("🌍 Reading & Resource Library")

    try:
        response = (
            supabase.table("learning_resources")
            .select("*")
            .eq("status", "approved")
            .order("created_at", desc=True)
            .execute()
        )

        resources = response.data or []

    except Exception as e:
        resources = []
        st.error(f"Could not load the resource library: {e}")

    if resources:
        for resource in resources:
            with st.container(border=True):
                st.markdown(f"**{resource.get('title', 'Learning resource')}**")
                st.caption(resource.get("category", "General"))
                st.write(resource.get("description", ""))

                if resource.get("resource_url"):
                    st.link_button(
                        "Open learning resource",
                        resource["resource_url"],
                        use_container_width=True
                    )

                if resource.get("licence"):
                    st.caption(f"Licence: {resource['licence']}")

    else:
        st.info(
            "Our resource library is growing. "
            "More approved learning materials will appear here."
        )

    st.divider()
    st.markdown("### 📤 Contribute a learning resource")

    st.write(
        "Have a useful article, guide or educational document? "
        "Share it with the EcoLoop community."
    )

    with st.form("learning_resource_upload", clear_on_submit=True):

        title = st.text_input("Resource title")
        description = st.text_area(
            "What will people learn from this resource?"
        )

        category = st.selectbox(
            "Learning category",
            [
                "Climate Action & Environment",
                "Governance & Civic Education",
                "Business & Entrepreneurship",
                "Technology, Innovation, Media & Arts"
            ]
        )

        licence = st.text_input(
            "Copyright / licence information",
            placeholder="e.g. CC BY 4.0, Public Domain, or permission obtained"
        )

        resource_url = st.text_input(
            "Resource link (optional)",
            placeholder="https://..."
        )

        uploaded_file = st.file_uploader(
            "Upload a PDF (optional)",
            type=["pdf"],
            help="Only upload material you created or have permission to share."
        )

        submitted = st.form_submit_button(
            "Submit for coordinator approval",
            use_container_width=True
        )

        if submitted:

            if not user_id:
                st.error("Please sign in before submitting a resource.")

            elif not title.strip() or not description.strip():
                st.warning("Please enter a title and description.")

            elif not licence.strip():
                st.warning("Please provide the resource's copyright or licence information.")

            elif not resource_url.strip() and uploaded_file is None:
                st.warning("Please provide a resource link or upload a PDF.")

            else:
                try:
                    file_path = None
                    final_url = resource_url.strip() or None

                    if uploaded_file is not None:
                        file_path = (
                            f"{user_id}/"
                            f"{uuid.uuid4().hex}_{uploaded_file.name}"
                        )

                        supabase.storage.from_(
                            "learning-resources"
                        ).upload(
                            file_path,
                            uploaded_file.getvalue(),
                            {"content-type": "application/pdf"}
                        )

                        final_url = (
                            supabase.storage.from_(
                                "learning-resources"
                            ).get_public_url(file_path)
                        )

                    supabase.table("learning_resources").insert({
                        "title": title.strip(),
                        "description": description.strip(),
                        "category": category,
                        "licence": licence.strip(),
                        "resource_url": final_url,
                        "file_path": file_path,
                        "submitted_by": user_id,
                        "status": "pending"
                    }).execute()

                    st.success(
                        "Thank you! Your resource has been submitted "
                        "for coordinator approval."
                    )

                except Exception as e:
                    st.error(f"Resource submission failed: {e}")


# ============================================================
# 6. COORDINATOR RESOURCE APPROVAL
# ============================================================

def _resource_approval(supabase):

    st.subheader("🛡️ Resource Approval Centre")

    try:
        response = (
            supabase.table("learning_resources")
            .select("*")
            .eq("status", "pending")
            .order("created_at", desc=True)
            .execute()
        )

        pending = response.data or []

    except Exception as e:
        st.error(f"Could not load pending resources: {e}")
        return

    if not pending:
        st.success("There are no resources waiting for approval.")
        return

    for resource in pending:

        with st.container(border=True):

            st.markdown(f"### {resource.get('title')}")
            st.write(resource.get("description", ""))
            st.caption(
                f"{resource.get('category')} • "
                f"Licence: {resource.get('licence')}"
            )

            if resource.get("resource_url"):
                st.link_button(
                    "Review resource",
                    resource["resource_url"]
                )

            col1, col2 = st.columns(2)

            with col1:
                if st.button(
                    "Approve",
                    key=f"approve_resource_{resource['id']}",
                    use_container_width=True
                ):
                    try:
                        supabase.table("learning_resources").update({
                            "status": "approved"
                        }).eq("id", resource["id"]).execute()

                        st.success("Resource approved.")
                        st.rerun()

                    except Exception as e:
                        st.error(f"Approval failed: {e}")

            with col2:
                if st.button(
                    "Reject",
                    key=f"reject_resource_{resource['id']}",
                    use_container_width=True
                ):
                    try:
                        supabase.table("learning_resources").update({
                            "status": "rejected"
                        }).eq("id", resource["id"]).execute()

                        st.warning("Resource rejected.")
                        st.rerun()

                    except Exception as e:
                        st.error(f"Rejection failed: {e}")


# ============================================================
# 7. MAIN EXPLORE & LEARN PAGE
# ============================================================

def render_explore_learn(
    supabase,
    user_id=None,
    user_name="EcoLoop Member",
    group_id=None,
    is_coordinator=False
):

    st.title("📚 Explore & Learn")

    st.write(
        "Learn something useful. Understand why it matters. "
        "Do something with that knowledge."
    )

    st.info(
        "🌱 Explore environmental knowledge, discover new ideas, "
        "test yourself and share what you know."
    )

    tabs = st.tabs([
        "Discover",
        "Quiz Centre",
        "Resource Library"
    ])

    with tabs[0]:
        _reading_library(
            supabase,
            user_id,
            group_id,
            user_name
        )

    with tabs[1]:
        _quiz_centre(
            supabase,
            user_id,
            group_id
        )

    with tabs[2]:
        _resource_library(
            supabase,
            user_id,
            is_coordinator
        )

    if is_coordinator:
        st.divider()
        with st.expander("Coordinator tools"):
            _resource_approval(supabase)

    st.divider()

    st.markdown(
        """
        <div style="text-align:center; padding:12px;">
            <b>Explore & Learn | EcoLoop Node</b><br>
            <small>Powered by Next Gen Impact Hub (NGIH)</small>
        </div>
        """,
        unsafe_allow_html=True
    )
