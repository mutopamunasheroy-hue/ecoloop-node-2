
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

    # =====================================================
    # PILLAR 1: CLIMATE ACTION & ENVIRONMENT (13)
    # =====================================================

    {
        "category": "Climate Action & Environment",
        "difficulty": "Beginner",
        "question": "What can happen when waste blocks drainage systems?",
        "options": [
            "It can contribute to flooding",
            "It improves water quality",
            "It creates more drainage space",
            "It makes waste disappear"
        ],
        "answer": 0,
        "explanation": "Blocked drains prevent water from flowing properly and can contribute to flooding."
    },
    {
        "category": "Climate Action & Environment",
        "difficulty": "Beginner",
        "question": "Which of these materials can commonly be recycled?",
        "options": [
            "Clean paper",
            "Dirty wastewater",
            "Food scraps mixed with chemicals",
            "Contaminated medical waste"
        ],
        "answer": 0,
        "explanation": "Clean paper can be processed into new paper products."
    },
    {
        "category": "Climate Action & Environment",
        "difficulty": "Beginner",
        "question": "What is biodiversity?",
        "options": [
            "The variety of living organisms in an area",
            "The number of buildings in a city",
            "The amount of plastic produced",
            "The study of machines only"
        ],
        "answer": 0,
        "explanation": "Biodiversity refers to the variety of plants, animals and other living organisms."
    },
    {
        "category": "Climate Action & Environment",
        "difficulty": "Intermediate",
        "question": "Which activity contributes most directly to human-caused climate change?",
        "options": [
            "Burning fossil fuels",
            "Separating recyclable waste",
            "Planting indigenous trees",
            "Collecting rainwater"
        ],
        "answer": 0,
        "explanation": "Burning coal, oil and gas releases greenhouse gases that contribute to global warming."
    },
    {
        "category": "Climate Action & Environment",
        "difficulty": "Beginner",
        "question": "What does the 3Rs approach to waste management stand for?",
        "options": [
            "Reduce, Reuse, Recycle",
            "Remove, Replace, Repair",
            "Reuse, Remove, Release",
            "Recover, Reject, Rebuild"
        ],
        "answer": 0,
        "explanation": "The 3Rs encourage reducing waste, reusing products and recycling suitable materials."
    },
    {
        "category": "Climate Action & Environment",
        "difficulty": "Intermediate",
        "question": "Why are wetlands important to communities?",
        "options": [
            "They help regulate water and support wildlife",
            "They increase plastic pollution",
            "They prevent all rainfall",
            "They eliminate the need for clean water"
        ],
        "answer": 0,
        "explanation": "Wetlands support biodiversity, store water and can help reduce flooding."
    },
    {
        "category": "Climate Action & Environment",
        "difficulty": "Intermediate",
        "question": "What is the purpose of separating waste at source?",
        "options": [
            "To make recovery and recycling easier",
            "To increase the amount of mixed waste",
            "To make all materials hazardous",
            "To prevent waste collection"
        ],
        "answer": 0,
        "explanation": "Separating materials where waste is produced makes recycling and safe disposal easier."
    },
    {
        "category": "Climate Action & Environment",
        "difficulty": "Beginner",
        "question": "Which energy source is renewable?",
        "options": [
            "Solar energy",
            "Coal",
            "Diesel",
            "Petrol"
        ],
        "answer": 0,
        "explanation": "Solar energy comes from sunlight, which is naturally replenished."
    },
    {
        "category": "Climate Action & Environment",
        "difficulty": "Intermediate",
        "question": "How can planting indigenous trees benefit Zimbabwean communities?",
        "options": [
            "By supporting local biodiversity and protecting ecosystems",
            "By increasing soil erosion",
            "By eliminating all insects",
            "By reducing the availability of oxygen"
        ],
        "answer": 0,
        "explanation": "Indigenous trees are adapted to local conditions and can provide habitats and other ecosystem benefits."
    },
    {
        "category": "Climate Action & Environment",
        "difficulty": "Advanced",
        "question": "What is climate adaptation?",
        "options": [
            "Adjusting to actual or expected climate impacts",
            "Stopping all weather changes",
            "Increasing dependence on fossil fuels",
            "Ignoring climate-related risks"
        ],
        "answer": 0,
        "explanation": "Adaptation involves preparing for and reducing harm from climate impacts such as droughts and floods."
    },
    {
        "category": "Climate Action & Environment",
        "difficulty": "Intermediate",
        "question": "Why should electronic waste be handled carefully?",
        "options": [
            "It may contain hazardous substances",
            "It always decomposes within days",
            "It is safe to burn in open spaces",
            "It cannot contain reusable materials"
        ],
        "answer": 0,
        "explanation": "Electronic waste can contain substances that harm people and the environment if poorly managed."
    },
    {
        "category": "Climate Action & Environment",
        "difficulty": "Advanced",
        "question": "What is the difference between climate mitigation and adaptation?",
        "options": [
            "Mitigation reduces climate change causes; adaptation manages its impacts",
            "Both mean increasing pollution",
            "Mitigation deals only with floods; adaptation only with recycling",
            "There is no difference between them"
        ],
        "answer": 0,
        "explanation": "Mitigation addresses greenhouse gas emissions, while adaptation helps communities cope with climate effects."
    },
    {
        "category": "Climate Action & Environment",
        "difficulty": "Advanced",
        "question": "What is a circular economy?",
        "options": [
            "An approach that keeps materials and products in use for longer",
            "An economy based entirely on dumping waste",
            "A system where every product is used once",
            "An approach that discourages repairing products"
        ],
        "answer": 0,
        "explanation": "A circular economy reduces waste through reuse, repair, refurbishment and recycling."
    },

    # =====================================================
    # PILLAR 2: GOVERNANCE & CIVIC EDUCATION (12)
    # =====================================================

    {
        "category": "Governance & Civic Education",
        "difficulty": "Beginner",
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
        "category": "Governance & Civic Education",
        "difficulty": "Beginner",
        "question": "What is civic responsibility?",
        "options": [
            "Taking part in actions that support society and the community",
            "Ignoring community problems",
            "Avoiding all public discussions",
            "Leaving every responsibility to businesses"
        ],
        "answer": 0,
        "explanation": "Civic responsibility involves contributing positively to society and respecting shared responsibilities."
    },
    {
        "category": "Governance & Civic Education",
        "difficulty": "Intermediate",
        "question": "Why should communities participate in local environmental decisions?",
        "options": [
            "They understand local needs and are affected by the decisions",
            "They should replace every public institution",
            "They should prevent others from expressing views",
            "They have no role in local development"
        ],
        "answer": 0,
        "explanation": "Community participation helps decisions reflect people's experiences, needs and priorities."
    },
    {
        "category": "Governance & Civic Education",
        "difficulty": "Intermediate",
        "question": "What does accountability in environmental governance mean?",
        "options": [
            "Institutions and leaders being answerable for their decisions and actions",
            "Leaders avoiding public questions",
            "Keeping all public decisions secret",
            "Allowing pollution without consequences"
        ],
        "answer": 0,
        "explanation": "Accountability requires decision-makers to explain and take responsibility for their actions."
    },
    {
        "category": "Governance & Civic Education",
        "difficulty": "Beginner",
        "question": "What is the purpose of reporting illegal dumping?",
        "options": [
            "To help relevant authorities address environmental problems",
            "To encourage more dumping",
            "To hide pollution from communities",
            "To prevent environmental monitoring"
        ],
        "answer": 0,
        "explanation": "Responsible reporting helps authorities and communities identify and respond to environmental violations."
    },
    {
        "category": "Governance & Civic Education",
        "difficulty": "Advanced",
        "question": "What does environmental justice focus on?",
        "options": [
            "Fair treatment and meaningful participation in environmental decisions",
            "Giving environmental protection only to wealthy communities",
            "Ignoring pollution in disadvantaged areas",
            "Removing communities from decision-making"
        ],
        "answer": 0,
        "explanation": "Environmental justice addresses fairness in environmental protection, decision-making and the distribution of environmental benefits and burdens."
    },
    {
        "category": "Governance & Civic Education",
        "difficulty": "Intermediate",
        "question": "Why are public consultations important?",
        "options": [
            "They allow affected people to contribute their views",
            "They prevent citizens from asking questions",
            "They guarantee that everyone agrees",
            "They remove the need for transparency"
        ],
        "answer": 0,
        "explanation": "Consultations provide opportunities for people to express concerns and influence decisions."
    },
    {
        "category": "Governance & Civic Education",
        "difficulty": "Beginner",
        "question": "Which action demonstrates good environmental citizenship?",
        "options": [
            "Participating in a community clean-up",
            "Dumping rubbish in a river",
            "Damaging public trees",
            "Encouraging pollution"
        ],
        "answer": 0,
        "explanation": "Environmental citizenship involves taking responsible action to protect shared surroundings."
    },
    {
        "category": "Governance & Civic Education",
        "difficulty": "Advanced",
        "question": "Why is transparency important in local waste-management programmes?",
        "options": [
            "It helps communities understand decisions and how resources are used",
            "It prevents citizens from monitoring projects",
            "It removes the need for reporting",
            "It allows funds to be used without explanation"
        ],
        "answer": 0,
        "explanation": "Transparency makes information accessible and supports public trust and accountability."
    },
    {
        "category": "Governance & Civic Education",
        "difficulty": "Intermediate",
        "question": "What is the role of local authorities in waste management?",
        "options": [
            "Supporting waste services, regulation and environmental management",
            "Encouraging illegal dumping",
            "Preventing all recycling initiatives",
            "Removing community participation"
        ],
        "answer": 0,
        "explanation": "Local authorities have important responsibilities in organising and regulating local public services, including waste management."
    },
    {
        "category": "Governance & Civic Education",
        "difficulty": "Advanced",
        "question": "What is participatory governance?",
        "options": [
            "Involving citizens in decisions that affect them",
            "Allowing only one leader to make every decision",
            "Preventing communities from accessing information",
            "Making decisions without consulting affected people"
        ],
        "answer": 0,
        "explanation": "Participatory governance creates opportunities for citizens to contribute to public decision-making."
    },
    {
        "category": "Governance & Civic Education",
        "difficulty": "Intermediate",
        "question": "Why should environmental information be accessible to young people?",
        "options": [
            "It helps them understand issues and participate responsibly",
            "It prevents them from asking questions",
            "It makes community action unnecessary",
            "It discourages environmental education"
        ],
        "answer": 0,
        "explanation": "Access to reliable information supports informed participation and responsible action."
    },

    # =====================================================
    # PILLAR 3: BUSINESS & ENTREPRENEURSHIP (12)
    # =====================================================

    {
        "category": "Business & Entrepreneurship",
        "difficulty": "Beginner",
        "question": "Which of these is an example of a green business?",
        "options": [
            "Illegal dumping",
            "A business collecting recyclable materials",
            "Burning waste in open spaces",
            "Throwing reusable materials away"
        ],
        "answer": 1,
        "explanation": "Collecting and processing recyclable materials can create economic value while reducing waste."
    },
    {
        "category": "Business & Entrepreneurship",
        "difficulty": "Beginner",
        "question": "What is entrepreneurship?",
        "options": [
            "Identifying opportunities and creating ventures to provide value",
            "Avoiding every business opportunity",
            "Copying products without understanding customers",
            "Waiting for someone else to solve every problem"
        ],
        "answer": 0,
        "explanation": "Entrepreneurship involves identifying opportunities, organising resources and creating value."
    },
    {
        "category": "Business & Entrepreneurship",
        "difficulty": "Intermediate",
        "question": "How can recycling create employment opportunities?",
        "options": [
            "Through collection, sorting, processing and selling recovered materials",
            "By eliminating every business activity",
            "By preventing people from repairing products",
            "By making all materials unusable"
        ],
        "answer": 0,
        "explanation": "Different stages of the recycling value chain can support jobs and businesses."
    },
    {
        "category": "Business & Entrepreneurship",
        "difficulty": "Beginner",
        "question": "What is a business customer?",
        "options": [
            "A person or organisation that buys a product or service",
            "A person who never uses a product",
            "Only the business owner",
            "A government regulation"
        ],
        "answer": 0,
        "explanation": "Customers are the people or organisations whose needs a business aims to serve."
    },
    {
        "category": "Business & Entrepreneurship",
        "difficulty": "Intermediate",
        "question": "What is a value proposition?",
        "options": [
            "The benefit or value a product or service offers customers",
            "The business owner's personal biography",
            "A list of unrelated expenses",
            "A record of every competitor's address"
        ],
        "answer": 0,
        "explanation": "A value proposition explains why customers might choose a particular product or service."
    },
    {
        "category": "Business & Entrepreneurship",
        "difficulty": "Intermediate",
        "question": "Why is market research useful before starting a recycling business?",
        "options": [
            "It helps identify customer needs, demand and competitors",
            "It guarantees immediate profits",
            "It removes all business risks",
            "It makes financial planning unnecessary"
        ],
        "answer": 0,
        "explanation": "Market research helps entrepreneurs understand the market before investing resources."
    },
    {
        "category": "Business & Entrepreneurship",
        "difficulty": "Beginner",
        "question": "What is revenue?",
        "options": [
            "Money earned from selling goods or services",
            "The total number of employees",
            "The amount of waste collected",
            "Money spent on all business expenses"
        ],
        "answer": 0,
        "explanation": "Revenue is income generated through business sales before expenses are deducted."
    },
    {
        "category": "Business & Entrepreneurship",
        "difficulty": "Advanced",
        "question": "What is the difference between revenue and profit?",
        "options": [
            "Profit is what remains after expenses are deducted from revenue",
            "Revenue is always lower than expenses",
            "Profit is the same as the number of customers",
            "Revenue includes only unpaid invoices"
        ],
        "answer": 0,
        "explanation": "Profit is calculated by subtracting relevant business costs from revenue."
    },
    {
        "category": "Business & Entrepreneurship",
        "difficulty": "Intermediate",
        "question": "What is one benefit of forming a cooperative among waste collectors?",
        "options": [
            "Members can pool resources and negotiate collectively",
            "Members must work without communication",
            "It prevents members from sharing information",
            "It removes the need for agreed responsibilities"
        ],
        "answer": 0,
        "explanation": "Cooperatives can help members combine resources, improve bargaining power and work towards shared goals."
    },
    {
        "category": "Business & Entrepreneurship",
        "difficulty": "Advanced",
        "question": "What does a sustainable business model aim to achieve?",
        "options": [
            "Long-term economic viability while considering social and environmental impacts",
            "Short-term sales regardless of environmental damage",
            "Growth without considering customers",
            "Profit through unlimited resource waste"
        ],
        "answer": 0,
        "explanation": "Sustainable business models consider financial performance alongside social and environmental responsibility."
    },
    {
        "category": "Business & Entrepreneurship",
        "difficulty": "Intermediate",
        "question": "Why might repairing products support a circular economy business?",
        "options": [
            "It extends product life and reduces the need for replacement",
            "It guarantees that every product becomes waste",
            "It increases demand for unnecessary disposal",
            "It prevents materials from being used again"
        ],
        "answer": 0,
        "explanation": "Repair keeps products useful for longer and can create services and employment."
    },
    {
        "category": "Business & Entrepreneurship",
        "difficulty": "Advanced",
        "question": "What is a business break-even point?",
        "options": [
            "The point where total revenue equals total costs",
            "The point where a business has no customers",
            "The point where expenses are always zero",
            "The point where a business stops recording sales"
        ],
        "answer": 0,
        "explanation": "At break-even, a business has covered its costs but has not yet made a profit."
    },

    # =====================================================
    # PILLAR 4: TECHNOLOGY, INNOVATION, MEDIA & ARTS (13)
    # =====================================================

    {
        "category": "Technology, Innovation, Media & Arts",
        "difficulty": "Beginner",
        "question": "How can technology support environmental protection?",
        "options": [
            "By helping monitor and organise waste collection",
            "By encouraging illegal dumping",
            "By preventing communities from sharing information",
            "By making recycling impossible"
        ],
        "answer": 0,
        "explanation": "Digital tools can support reporting, monitoring and coordination of environmental activities."
    },
    {
        "category": "Technology, Innovation, Media & Arts",
        "difficulty": "Beginner",
        "question": "What is digital innovation?",
        "options": [
            "Using digital technologies in new or improved ways",
            "Avoiding all forms of technology",
            "Using computers only for decoration",
            "Preventing people from sharing information"
        ],
        "answer": 0,
        "explanation": "Digital innovation applies technology to improve products, services and processes."
    },
    {
        "category": "Technology, Innovation, Media & Arts",
        "difficulty": "Intermediate",
        "question": "How can QR codes help an environmental project?",
        "options": [
            "They can link users to digital information and resources",
            "They automatically remove waste",
            "They replace the need for environmental education",
            "They prevent people from accessing websites"
        ],
        "answer": 0,
        "explanation": "QR codes can provide quick access to information, instructions and digital resources."
    },
    {
        "category": "Technology, Innovation, Media & Arts",
        "difficulty": "Intermediate",
        "question": "What is the purpose of collecting data in a waste-management app?",
        "options": [
            "To track activities and support informed decisions",
            "To make every report inaccurate",
            "To prevent users from understanding progress",
            "To eliminate the need for verification"
        ],
        "answer": 0,
        "explanation": "Reliable data helps projects measure performance, identify gaps and improve services."
    },
    {
        "category": "Technology, Innovation, Media & Arts",
        "difficulty": "Beginner",
        "question": "What is digital literacy?",
        "options": [
            "The ability to use digital tools and information effectively and responsibly",
            "The ability to operate only one type of phone",
            "The ability to avoid all online information",
            "The ability to create passwords for other people"
        ],
        "answer": 0,
        "explanation": "Digital literacy includes using technology, evaluating information and behaving responsibly online."
    },
    {
        "category": "Technology, Innovation, Media & Arts",
        "difficulty": "Advanced",
        "question": "Why is data verification important in environmental reporting?",
        "options": [
            "It helps ensure that reported information is accurate and trustworthy",
            "It guarantees that every submitted claim is true",
            "It makes evidence unnecessary",
            "It allows incorrect records to remain unchallenged"
        ],
        "answer": 0,
        "explanation": "Verification helps identify errors and strengthens confidence in environmental records."
    },
    {
        "category": "Technology, Innovation, Media & Arts",
        "difficulty": "Intermediate",
        "question": "What is citizen science?",
        "options": [
            "Public participation in scientific research and data collection",
            "Science conducted only by private companies",
            "A system that prevents communities from collecting observations",
            "The use of technology without gathering information"
        ],
        "answer": 0,
        "explanation": "Citizen science allows members of the public to contribute observations and data to research."
    },
    {
        "category": "Technology, Innovation, Media & Arts",
        "difficulty": "Beginner",
        "question": "How can environmental storytelling influence communities?",
        "options": [
            "By helping people understand environmental issues through stories",
            "By hiding every environmental problem",
            "By discouraging public awareness",
            "By replacing evidence with rumours"
        ],
        "answer": 0,
        "explanation": "Stories can make environmental issues understandable, relatable and memorable."
    },
    {
        "category": "Technology, Innovation, Media & Arts",
        "difficulty": "Intermediate",
        "question": "What should someone do before sharing an environmental claim online?",
        "options": [
            "Check the information against reliable sources",
            "Share it immediately because it is popular",
            "Remove the original source",
            "Change the facts to attract attention"
        ],
        "answer": 0,
        "explanation": "Checking reliable sources helps reduce the spread of misinformation."
    },
    {
        "category": "Technology, Innovation, Media & Arts",
        "difficulty": "Advanced",
        "question": "What is artificial intelligence in simple terms?",
        "options": [
            "Computer systems performing tasks that normally require human-like intelligence",
            "A machine that always makes perfect decisions",
            "A type of renewable energy",
            "A system that operates without data or instructions"
        ],
        "answer": 0,
        "explanation": "AI refers to computer systems designed to perform tasks such as recognising patterns, generating content or making predictions."
    },
    {
        "category": "Technology, Innovation, Media & Arts",
        "difficulty": "Advanced",
        "question": "How could mapping technology help a community waste-management programme?",
        "options": [
            "By identifying collection points and areas with service gaps",
            "By making locations impossible to identify",
            "By preventing route planning",
            "By replacing all community participation"
        ],
        "answer": 0,
        "explanation": "Mapping can help visualise waste collection locations, routes and areas needing attention."
    },
    {
        "category": "Technology, Innovation, Media & Arts",
        "difficulty": "Intermediate",
        "question": "Why is user feedback important when designing an environmental app?",
        "options": [
            "It helps developers understand users' needs and improve the app",
            "It guarantees that the first version is perfect",
            "It removes the need for testing",
            "It prevents users from reporting problems"
        ],
        "answer": 0,
        "explanation": "Feedback helps identify usability problems and features that would make the app more useful."
    },
    {
        "category": "Technology, Innovation, Media & Arts",
        "difficulty": "Advanced",
        "question": "What is one important ethical responsibility when collecting users' data?",
        "options": [
            "Protecting personal information and limiting unnecessary access",
            "Publishing private information without permission",
            "Collecting as much personal information as possible",
            "Sharing passwords between users"
        ],
        "answer": 0,
        "explanation": "Responsible data practices protect privacy and help maintain user trust."
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
    # LOAD THE MEMBER'S APPROVED GROUPS
    approved_groups = []

    if user_id:
        try:
            memberships = (
                supabase.table("group_memberships")
                .select("group_id")
                .eq("user_id", user_id)
                .eq("status", "approved")
                .execute()
            )

            group_ids = list({
                item["group_id"]
                for item in (memberships.data or [])
                if item.get("group_id")
            })

            if group_ids:
                response = (
                    supabase.table("community_groups")
                    .select("*")
                    .in_("id", group_ids)
                    .execute()
                )

                approved_groups = response.data or []
    # SELECT WHERE THIS LEARNING ACTIVITY COUNTS
    group_choices = [None] + approved_groups

    selected_group = st.selectbox(
        "Where should this learning activity count?",
        options=group_choices,
        format_func=lambda group: (
            f"{user_name} (Individual)"
            if group is None
            else (
                group.get("group_name")
                or group.get("name")
                or group.get("title")
                or "Environmental Community Group"
            )
        ),
        key="learning_group_choice"
    )

    group_id = selected_group.get("id") if selected_group else None
        except Exception as e:
            st.warning(f"Could not load your approved groups: {e}")
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

    st.write(
        "Explore approved learning materials from the EcoLoop "
        "community. Download PDFs to read them offline."
    )

    # --------------------------------------------------------
    # DISPLAY APPROVED RESOURCES
    # --------------------------------------------------------

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

                st.markdown(
                    f"### 📖 {resource.get('title', 'Learning resource')}"
                )

                st.caption(
                    resource.get("category", "General")
                )

                st.write(
                    resource.get("description", "")
                )

                # DOWNLOAD PDF FROM PRIVATE STORAGE
                file_path = resource.get("file_path")

                if file_path:

                    try:
                        pdf_bytes = (
                            supabase.storage
                            .from_("learning-resources")
                            .download(file_path)
                        )

                        st.download_button(
                            label="⬇️ Download PDF for offline reading",
                            data=pdf_bytes,
                            file_name=(
                                resource.get("title", "EcoLoop resource")
                                .strip()
                                .replace("/", "-")
                                + ".pdf"
                            ),
                            mime="application/pdf",
                            key=f"download_resource_{resource['id']}",
                            use_container_width=True
                        )

                    except Exception as e:
                        st.warning(
                            "This PDF could not be downloaded right now. "
                            "Please try again later."
                        )

                # EXTERNAL RESOURCE LINK
                if resource.get("resource_url"):

                    st.link_button(
                        "🔗 Open online resource",
                        resource["resource_url"],
                        use_container_width=True
                    )

                if resource.get("licence"):

                    st.caption(
                        f"Copyright / Licence: {resource['licence']}"
                    )

    else:

        st.info(
            "Our resource library is growing. "
            "More approved learning materials will appear here."
        )

    st.divider()

    # --------------------------------------------------------
    # MEMBER RESOURCE SUBMISSIONS
    # --------------------------------------------------------

    st.markdown("### 📤 Contribute a learning resource")

    st.write(
        "Have a useful article, guide or educational document? "
        "Share it with the EcoLoop community for review."
    )

    with st.form(
        "learning_resource_upload",
        clear_on_submit=True
    ):

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
            placeholder=(
                "e.g. CC BY 4.0, Public Domain, "
                "or permission obtained"
            )
        )

        resource_url = st.text_input(
            "Resource link (optional)",
            placeholder="https://..."
        )

        uploaded_file = st.file_uploader(
            "Upload a PDF (optional)",
            type=["pdf"],
            help=(
                "Only upload material you created "
                "or have permission to share."
            )
        )

        submitted = st.form_submit_button(
            "Submit for coordinator approval",
            use_container_width=True
        )

        if submitted:

            if not user_id:

                st.error(
                    "Please sign in before submitting a resource."
                )

            elif not title.strip() or not description.strip():

                st.warning(
                    "Please enter a title and description."
                )

            elif not licence.strip():

                st.warning(
                    "Please provide the resource's copyright "
                    "or licence information."
                )

            elif not resource_url.strip() and uploaded_file is None:

                st.warning(
                    "Please provide a resource link or upload a PDF."
                )

            else:

                try:

                    file_path = None
                    final_url = resource_url.strip() or None

                    # UPLOAD PDF TO PRIVATE SUPABASE STORAGE
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
                            {
                                "content-type": "application/pdf"
                            }
                        )

                    # SAVE RESOURCE DETAILS
                    supabase.table(
                        "learning_resources"
                    ).insert({

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

                    st.info(
                        "Once approved, it will appear in the "
                        "Reading & Resource Library."
                    )

                except Exception as e:

                    st.error(
                        f"Resource submission failed: {e}"
                    )

        

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
