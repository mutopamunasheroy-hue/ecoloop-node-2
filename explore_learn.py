# ============================================================
# ECOLOOP NODE — EXPLORE & LEARN
# Powered by Next Gen Impact Hub (NGIH)
# ============================================================

import streamlit as st
import uuid
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


# ============================================================
# 1. PILLARS AND 50 READING MATERIALS
# ============================================================

PILLARS = [
    "Climate Action & Environment",
    "Governance & Civic Education",
    "Business & Entrepreneurship",
    "Technology, Innovation, Media & Arts"
]


# Each topic retains its original position so existing
# completion IDs eco_001 to eco_050 remain unchanged.

READING_TOPICS = [
    # ENVIRONMENT — 13
    ("Where does our waste go?", PILLARS[0],
     "Understand what happens when waste is poorly managed.",
     "Waste can end up in streets, drainage systems, rivers and open spaces. Poor disposal affects ecosystems, public health and community wellbeing.",
     "Identify one waste-management problem in your community."),

    ("Understanding climate change", PILLARS[0],
     "Explore the causes and effects of climate change.",
     "Climate change refers to long-term changes in temperatures and weather patterns. Human activities, especially burning fossil fuels, are the main cause of recent global warming.",
     "Identify one climate-related challenge affecting your area."),

    ("The importance of biodiversity", PILLARS[0],
     "Discover why different forms of life matter.",
     "Biodiversity includes the variety of plants, animals and microorganisms. Healthy ecosystems support food production, clean water, soil health and livelihoods.",
     "Name three forms of biodiversity found in Zimbabwe."),

    ("The 3Rs of waste management", PILLARS[0],
     "Learn how to reduce the amount of waste produced.",
     "Reduce means using fewer resources. Reuse means using items again. Recycle means processing suitable materials into new products.",
     "Choose one item you could reuse instead of throwing it away."),

    ("Protecting rivers and water sources", PILLARS[0],
     "Understand why clean water sources need protection.",
     "Dumping waste and chemicals into water sources threatens people, animals and aquatic ecosystems. Communities can help protect water through responsible disposal and reporting pollution.",
     "Identify a water source that needs protection."),

    ("Why wetlands matter", PILLARS[0],
     "Explore the value of wetlands.",
     "Wetlands store water, support wildlife, filter some pollutants and can reduce flood impacts. Their destruction can weaken important natural systems.",
     "Find out whether your community has a wetland."),

    ("Indigenous trees and ecosystems", PILLARS[0],
     "Understand the value of indigenous trees.",
     "Indigenous trees are naturally suited to local environments. They can provide habitats, shade, food, soil protection and cultural value.",
     "Learn the name of one indigenous tree in your area."),

    ("Understanding air pollution", PILLARS[0],
     "Explore common sources and effects of air pollution.",
     "Smoke, vehicle emissions, industrial activities and open waste burning can affect air quality. Reducing pollution helps protect respiratory health and ecosystems.",
     "Identify one local source of air pollution."),

    ("Electronic waste and responsible disposal", PILLARS[0],
     "Learn why electronic waste needs special attention.",
     "Old phones, batteries and electronic equipment may contain hazardous substances as well as recoverable materials. They should be handled through appropriate collection and recycling channels.",
     "Identify an appropriate electronic-waste collection option."),

    ("Soil conservation", PILLARS[0],
     "Discover why healthy soil matters.",
     "Soil supports agriculture, stores water and provides habitats. Erosion, pollution and poor land management can reduce soil quality.",
     "Suggest one way to protect soil in your community."),

    ("Climate adaptation", PILLARS[0],
     "Understand how communities prepare for climate impacts.",
     "Adaptation means adjusting to actual or expected climate impacts. Examples include water conservation, climate-resilient agriculture and improved disaster preparedness.",
     "Suggest one way households can prepare for drought."),

    ("The circular economy", PILLARS[0],
     "Explore an economy that reduces waste.",
     "A circular economy aims to keep products and materials useful for longer through repair, reuse, refurbishment and recycling. It reduces dependence on constant extraction of new resources.",
     "Think of one product that could be repaired rather than replaced."),

    ("Community clean-up campaigns", PILLARS[0],
     "Understand how organised clean-ups can help.",
     "Community clean-ups can improve shared spaces and raise awareness. They work best when combined with waste prevention, collection systems and responsible disposal.",
     "Identify a suitable place for a community clean-up."),

    # GOVERNANCE — 12
    ("Who is responsible for a clean community?", PILLARS[1],
     "Explore shared environmental responsibility.",
     "Individuals, businesses, communities and public institutions all have roles in environmental protection. Cooperation helps create cleaner and healthier settlements.",
     "Identify one environmental responsibility you can take on."),

    ("Understanding civic responsibility", PILLARS[1],
     "Learn how citizens contribute to society.",
     "Civic responsibility includes respecting laws, participating in community affairs, protecting shared resources and treating others fairly.",
     "Describe one way young people can contribute to their community."),

    ("What is environmental governance?", PILLARS[1],
     "Explore how environmental decisions are made.",
     "Environmental governance includes the institutions, rules and processes used to manage natural resources and environmental issues. Good governance requires participation, accountability and transparency.",
     "Identify an environmental issue requiring better local coordination."),

    ("Community participation in decision-making", PILLARS[1],
     "Understand why community voices matter.",
     "People affected by decisions should have meaningful opportunities to express their needs and experiences. Participation can improve the relevance and fairness of development programmes.",
     "Suggest one way residents can contribute to local decisions."),

    ("Transparency and accountability", PILLARS[1],
     "Learn why public institutions should explain their actions.",
     "Transparency makes information accessible. Accountability means decision-makers can be questioned and held responsible for their actions.",
     "Think of one question residents could ask about a public service."),

    ("The role of local authorities", PILLARS[1],
     "Understand local government responsibilities.",
     "Local authorities play important roles in public services, planning, sanitation and local environmental management. Their work affects everyday community wellbeing.",
     "Identify one local service that affects environmental health."),

    ("Environmental rights and responsibilities", PILLARS[1],
     "Explore the relationship between rights and duties.",
     "People have interests in a clean and healthy environment. Protecting environmental wellbeing also requires responsible conduct and respect for the rights of others.",
     "Explain why environmental protection is a shared responsibility."),

    ("Youth participation in governance", PILLARS[1],
     "Discover how young people can influence decisions.",
     "Young people can contribute through consultations, civic education, community projects and constructive engagement with institutions.",
     "Identify one issue young people should raise with local leaders."),

    ("Public consultations", PILLARS[1],
     "Understand how public consultations work.",
     "Consultations allow affected people to share opinions before decisions are made. Meaningful consultation requires accessible information and genuine consideration of feedback.",
     "Think of a local development issue that needs consultation."),

    ("Environmental justice", PILLARS[1],
     "Explore fairness in environmental protection.",
     "Environmental justice concerns fair treatment and meaningful participation. No community should carry unfair environmental burdens because of poverty or limited influence.",
     "Identify an example of unequal exposure to environmental problems."),

    ("Community reporting and responsible citizenship", PILLARS[1],
     "Learn how to report community problems constructively.",
     "Responsible reporting provides clear information about a concern and, where possible, evidence. Reports should protect privacy and avoid spreading unverified accusations.",
     "Identify the appropriate channel for reporting illegal dumping."),

    ("Peaceful dialogue and community problem-solving", PILLARS[1],
     "Explore how communities can resolve disagreements.",
     "Different groups may have different priorities. Respectful dialogue, listening and fair processes help communities identify practical solutions.",
     "Suggest one way to resolve a disagreement about a community project."),

    # BUSINESS — 12
    ("Can waste become wealth?", PILLARS[2],
     "Discover how recycling can create economic opportunities.",
     "Recovered materials can support collection, sorting, repair, recycling and upcycling businesses. These activities can create value while reducing waste.",
     "Think of one small environmental business idea."),

    ("Introduction to entrepreneurship", PILLARS[2],
     "Understand how entrepreneurs identify opportunities.",
     "Entrepreneurship involves identifying a need, developing a solution, organising resources and creating value for customers or communities.",
     "Identify one problem that could become a business opportunity."),

    ("What is a green business?", PILLARS[2],
     "Explore businesses that consider environmental impacts.",
     "Green businesses provide products or services that reduce environmental harm or support sustainable resource use. They still need sound planning and financial management.",
     "Name one green business that could operate in your area."),

    ("Understanding customers", PILLARS[2],
     "Learn why businesses need to understand customers.",
     "Customers have needs, preferences and challenges. Businesses that listen to customers can design more useful products and services.",
     "Identify the likely customers for a recycling service."),

    ("Market research for beginners", PILLARS[2],
     "Discover how to investigate a business opportunity.",
     "Market research helps entrepreneurs understand demand, competitors, prices and customer preferences before committing resources.",
     "Write one question you would ask potential customers."),

    ("Understanding revenue and profit", PILLARS[2],
     "Learn the difference between sales income and profit.",
     "Revenue is money earned from sales. Profit is what remains after relevant costs are deducted. A business must understand both to assess its performance.",
     "Name two costs a recycling business might face."),

    ("Building a simple business model", PILLARS[2],
     "Explore how a business creates and delivers value.",
     "A business model explains what a business offers, who it serves, how it operates and how it earns income or sustains its activities.",
     "Describe a simple environmental service you could offer."),

    ("Cooperatives and collective enterprise", PILLARS[2],
     "Understand how people can work together economically.",
     "Cooperatives allow members to pool resources, share responsibilities and pursue common economic goals. Clear rules and accountability are important.",
     "Identify one advantage of a waste-collectors' cooperative."),

    ("The value of repairing products", PILLARS[2],
     "Explore repair as an economic opportunity.",
     "Repair services extend product life and reduce unnecessary disposal. They can also create practical skills, customer relationships and employment.",
     "Identify one item commonly discarded that could be repaired."),

    ("Financial planning for small projects", PILLARS[2],
     "Learn why projects need realistic budgets.",
     "Financial planning identifies expected costs, available resources and possible income. It helps project teams avoid spending beyond their means.",
     "List one likely cost of running a community recycling project."),

    ("Social entrepreneurship", PILLARS[2],
     "Understand businesses that address social problems.",
     "Social entrepreneurs develop practical solutions to social or environmental challenges while building a model that can continue operating over time.",
     "Identify a social problem that could be addressed through enterprise."),

    ("Sustainable business practices", PILLARS[2],
     "Explore long-term business responsibility.",
     "Sustainable businesses consider economic performance alongside social and environmental effects. Responsible sourcing, fair treatment and reduced waste can strengthen long-term value.",
     "Suggest one sustainable practice for a small business."),

    # TECHNOLOGY — 13
    ("Technology for a greener future", PILLARS[3],
     "Discover how innovation can improve environmental protection.",
     "Technology can help communities monitor waste, organise collections, share information and understand environmental problems.",
     "Suggest one digital solution to a waste problem."),

    ("What is digital innovation?", PILLARS[3],
     "Understand how digital tools can improve services.",
     "Digital innovation applies technology in new or improved ways to solve problems. Useful innovation begins with understanding people's needs.",
     "Identify one everyday problem a simple app could help solve."),

    ("How QR codes work", PILLARS[3],
     "Explore how QR codes connect physical and digital information.",
     "QR codes can direct users to websites, learning materials, registration forms or instructions. The information behind the code should be accurate and safe.",
     "Suggest one useful place to display an environmental QR code."),

    ("Why environmental data matters", PILLARS[3],
     "Understand how data supports better decisions.",
     "Reliable data helps projects track activities, identify gaps and measure progress. Poor-quality data can lead to misleading conclusions.",
     "Name two pieces of information a waste-management project should record."),

    ("Digital literacy", PILLARS[3],
     "Learn how to use digital information responsibly.",
     "Digital literacy includes using devices, evaluating online information, communicating responsibly and protecting personal information.",
     "Name one way to check whether online information is reliable."),

    ("Data privacy and online safety", PILLARS[3],
     "Understand why personal information needs protection.",
     "Apps should collect only necessary information, explain how it is used and restrict access. Users should protect passwords and avoid sharing private details publicly.",
     "Identify one type of personal information an app should protect."),

    ("Citizen science", PILLARS[3],
     "Discover how communities can contribute to research.",
     "Citizen science involves members of the public helping collect observations or data for research. Clear methods improve the usefulness of contributions.",
     "Suggest one environmental observation residents could record."),

    ("Environmental storytelling", PILLARS[3],
     "Explore how stories communicate environmental issues.",
     "Stories, photographs and creative media can make complex environmental issues easier to understand. Responsible storytelling should respect people's dignity and use accurate information.",
     "Think of a local environmental story worth sharing."),

    ("Media literacy and misinformation", PILLARS[3],
     "Learn to evaluate claims before sharing them.",
     "Online claims can be misleading or incomplete. Checking original sources, dates and reliable evidence helps reduce misinformation.",
     "Name one step you should take before sharing an environmental claim."),

    ("Introduction to artificial intelligence", PILLARS[3],
     "Understand AI in simple terms.",
     "Artificial intelligence describes computer systems designed to perform tasks such as recognising patterns, generating content and making predictions. AI outputs still need human judgement.",
     "Suggest one responsible use of AI in environmental work."),

    ("Mapping technology for communities", PILLARS[3],
     "Explore how maps can support local planning.",
     "Digital maps can show collection points, service gaps and environmental concerns. Location data should be collected and shared responsibly.",
     "Identify one type of environmental location worth mapping."),

    ("Design thinking and problem-solving", PILLARS[3],
     "Learn a human-centred approach to innovation.",
     "Design thinking begins by understanding people, defining a problem, developing ideas, testing solutions and improving them through feedback.",
     "Identify one person you would consult before designing an environmental app."),

    ("Arts, creativity and climate action", PILLARS[3],
     "Explore how creative work can encourage environmental action.",
     "Music, visual arts, theatre, photography and design can communicate ideas and encourage participation. Creative messages are strongest when they are accurate and inclusive.",
     "Suggest a creative campaign to promote responsible waste management.")
]


# Additional lesson explanations make the materials more useful
# without changing the original lesson titles or their IDs.

LESSON_DETAILS = {
    "Where does our waste go?": (
        "Waste does not simply disappear when it leaves a household or business. It may be collected, transported, sorted, recycled, treated or taken to a disposal site. When collection systems are unreliable, rubbish can accumulate in open spaces and drainage channels. Some materials remain in the environment for a long time, while others can break down into smaller pieces that are difficult to remove.",
        "In Zimbabwean communities, waste management is connected to public health, drainage, water quality and the appearance of neighbourhoods. Understanding the journey of waste helps residents ask better questions about collection services and disposal practices.",
        "Follow the journey of one item you throw away. Find out whether it is collected, reused, recycled or disposed of."
    ),
    "Understanding climate change": (
        "The climate is the long-term pattern of temperature, rainfall, winds and other weather conditions. Greenhouse gases trap some heat in the atmosphere. Human activities such as burning coal, oil and gas, deforestation and some agricultural practices increase these gases. This strengthens the natural greenhouse effect and contributes to global warming.",
        "Climate change can affect rainfall patterns, agriculture, water availability, ecosystems and livelihoods. Communities that depend on rain-fed farming or have limited resources to prepare for extreme weather may face particular challenges.",
        "Separate a weather event from a long-term climate trend. Then identify one practical way your community could prepare for changing conditions."
    ),
    "The importance of biodiversity": (
        "Biodiversity exists at different levels: variety within a species, variety between species and variety of ecosystems. Plants, insects, birds, mammals, fungi and microorganisms all contribute to ecological processes. Pollination, decomposition, nutrient cycling and natural pest control are examples of services supported by biodiversity.",
        "Zimbabwe's natural heritage includes woodlands, grasslands, wetlands, rivers and wildlife. Biodiversity supports tourism, agriculture, cultural identity and the resilience of ecosystems. Habitat destruction, pollution, invasive species and unsustainable harvesting can threaten it.",
        "Choose a local plant or animal and investigate the role it plays in its ecosystem."
    ),
    "The 3Rs of waste management": (
        "The 3Rs are often presented in order of priority. Reducing waste prevents unnecessary consumption in the first place. Reusing keeps an item serving a purpose without major processing. Recycling turns suitable discarded materials into inputs for new products. Recycling is useful, but it still requires energy, sorting and suitable facilities.",
        "A community can make progress by preventing avoidable packaging, carrying reusable bags and containers, repairing useful items and separating recyclable materials where collection services exist. The best option depends on the material and local facilities.",
        "For one week, notice what you throw away. Identify one item you could avoid buying, reuse or send for appropriate recycling."
    ),
    "Protecting rivers and water sources": (
        "Rivers, streams, dams, groundwater and springs support people and ecosystems. Pollution can come from poorly managed waste, untreated sewage, agricultural chemicals, industrial discharge and soil erosion. Pollutants may travel downstream, affecting communities far from the original source.",
        "Clean water is essential for drinking, food production, sanitation and biodiversity. Protecting water sources requires responsible household practices, effective public services, monitoring and reporting of pollution through appropriate channels.",
        "Identify a nearby water source and list two possible threats to its quality. Do not enter unsafe areas or handle unknown pollutants."
    ),
    "Why wetlands matter": (
        "Wetlands are areas where water influences the soil and supports plants adapted to wet conditions. They include marshes, swamps and other seasonally or permanently wet environments. Wetlands can store water, slow runoff, provide habitat and trap some sediments. Their ability to perform these functions depends on their condition.",
        "When wetlands are drained, filled or polluted, communities can lose natural water storage and important wildlife habitats. Wetlands should therefore be considered in land-use planning rather than treated as unused land.",
        "Find out whether a wetland exists near your community and learn what plants, birds or other wildlife depend on it."
    ),
    "Indigenous trees and ecosystems": (
        "Indigenous trees are species that naturally occur in a particular region. They are part of local ecological relationships and may provide food, nesting places and shelter for wildlife. Their roots can help stabilise soil, while their leaves contribute organic matter as they decompose.",
        "Local tree species can be valuable in restoration projects because they are adapted to regional conditions. However, planting the right species in the right place matters. Protecting existing mature trees is also important because replacement trees take time to grow.",
        "Learn the name of a local indigenous tree, what it provides to wildlife and whether it is suitable for planting in your area."
    ),
    "Understanding air pollution": (
        "Air pollution occurs when harmful substances enter the air at levels that can affect people or the environment. Sources include vehicle exhaust, industrial emissions, dust, household fuels and the burning of waste. Pollution can be concentrated near roads, workplaces or places where burning occurs.",
        "Poor air quality can affect breathing, aggravate existing health problems and damage plants and ecosystems. Preventing open waste burning, maintaining vehicles and improving cleaner energy options can help reduce exposure.",
        "Observe possible sources of smoke or dust in your area and identify a responsible way to raise concerns."
    ),
    "Electronic waste and responsible disposal": (
        "Electronic waste includes discarded phones, computers, chargers, televisions, batteries and other electrical equipment. Some devices contain metals and components that can be recovered, while others may contain substances that require careful handling. Breaking, burning or dumping electronic items can create environmental and safety risks.",
        "As digital devices become more common, communities need reliable ways to repair, reuse, collect and recycle them. A device that no longer works for one person may still be repairable or useful for parts.",
        "Before discarding an electronic item, consider whether it can be repaired, safely reused or taken to a recognised collection point."
    ),
    "Soil conservation": (
        "Soil is a living system containing minerals, organic matter, water, air and organisms. It supports plant growth and helps regulate water movement. Soil erosion occurs when wind or water removes topsoil. Poor land management, loss of vegetation and some forms of pollution can reduce soil quality.",
        "Healthy soil supports farming, gardens, trees and natural habitats. In areas affected by erosion, productive land can become less useful and sediment can enter rivers and dams.",
        "Identify a place where soil is exposed or eroding. Suggest a suitable prevention measure, such as maintaining vegetation or improving water flow."
    ),
    "Climate adaptation": (
        "Climate adaptation involves adjusting systems and activities to reduce harm from current or expected climate impacts. Examples include storing water safely, using suitable crop varieties, improving drainage, protecting shade trees and strengthening early-warning arrangements. Adaptation should respond to local risks rather than rely on one solution for every place.",
        "For communities facing drought, heat, floods or changing rainfall, preparation can protect livelihoods and essential services. Local knowledge is valuable when combined with reliable climate information and inclusive planning.",
        "Choose one climate risk in your area and identify a realistic action households, schools or community groups could take."
    ),
    "The circular economy": (
        "A circular economy aims to prevent waste and keep products, components and materials in use. It encourages designing products that last, maintaining and repairing them, sharing or reusing items, and recovering materials when products reach the end of their useful life. It is different from a linear system that takes resources, makes products and then discards them.",
        "Circular approaches can create opportunities for repairers, collectors, recyclers and small enterprises. They can also reduce demand for new raw materials. Not every material can be recycled indefinitely, so preventing waste and extending product life remain important.",
        "Choose an everyday product and map how it could be maintained, repaired, reused and eventually recovered."
    ),
    "Community clean-up campaigns": (
        "A clean-up campaign is an organised activity in which people work together to remove litter or improve a shared space. Effective campaigns begin with a clear location, permission where needed, safe working arrangements and a plan for collecting and disposing of the waste. Volunteers should not handle hazardous or unknown materials.",
        "Clean-ups can build cooperation and draw attention to service gaps. However, they are not a permanent replacement for reliable collection, waste prevention and responsible disposal systems.",
        "Plan a small clean-up by identifying the location, people to consult, materials needed and the safe disposal arrangement."
    ),
    "Who is responsible for a clean community?": (
        "Environmental responsibility is shared, but different actors have different duties and capacities. Households can dispose of waste responsibly, businesses can manage their waste and reduce pollution, community groups can organise awareness activities, and public institutions can provide services and enforce relevant rules.",
        "A clean community depends on cooperation and clear responsibilities. Blaming one group alone rarely solves a problem when collection systems, public behaviour, infrastructure and enforcement all influence the outcome.",
        "Choose one local environmental problem and identify what residents, businesses and public institutions could each contribute."
    ),
    "Understanding civic responsibility": (
        "Civic responsibility describes the ways people contribute to the wellbeing of society. It includes respecting the rights of others, following lawful processes, protecting shared spaces, seeking reliable information and taking part in community affairs. It can involve everyday actions as well as formal participation.",
        "Young people can contribute through volunteering, school and community initiatives, respectful discussion and learning about how public decisions are made. Participation should be safe, constructive and inclusive.",
        "Identify one issue affecting your community and one peaceful, constructive way young people could help address it."
    ),
    "What is environmental governance?": (
        "Environmental governance is the way decisions about natural resources and environmental protection are made and implemented. It involves laws, policies, public institutions, businesses, communities and the processes through which they interact. Good governance requires clear responsibilities, access to information and ways to raise concerns.",
        "Waste collection, land use, water protection and pollution control all depend on decisions made by different actors. Poor coordination can leave gaps, while accountable cooperation can improve services.",
        "Choose an environmental issue and identify the institutions or groups that should work together to address it."
    ),
    "Community participation in decision-making": (
        "Participation means more than simply informing people after a decision has already been made. It can include sharing information, collecting views, discussing alternatives and involving affected groups in planning and monitoring. Participation should be accessible to people with different ages, abilities and circumstances.",
        "Residents often understand local conditions that may not be visible to outside planners. Their knowledge can help projects avoid unsuitable locations, overlooked needs or unintended consequences.",
        "Think of a proposed community project. Identify who should be consulted and how their views could influence the final decision."
    ),
    "Transparency and accountability": (
        "Transparency means that relevant information about decisions, processes and resources is accessible and understandable. Accountability means that people and institutions can explain their actions and be held responsible for meeting their duties. Both require clear records and fair ways to ask questions.",
        "In a community project, people should be able to understand its goals, budget, activities and results. This helps build trust and makes it easier to identify mistakes or misuse of resources.",
        "Write down two reasonable questions residents could ask when reviewing a community waste-management project."
    ),
    "The role of local authorities": (
        "Local authorities are responsible for a range of local public functions, which may include planning, public health, sanitation, waste services and management of public spaces. Their exact responsibilities are shaped by the relevant laws, policies and local arrangements.",
        "Residents experience local services directly. Constructive communication between communities and local authorities can help identify service gaps, clarify responsibilities and improve planning.",
        "Identify one local service connected to environmental health and find out how residents can raise a concern about it."
    ),
    "Environmental rights and responsibilities": (
        "Environmental rights concern people's ability to live in conditions that support health and wellbeing, and to access relevant environmental information and participation processes. Responsibilities include respecting other people's rights and avoiding actions that harm shared resources.",
        "Rights and responsibilities are connected. Protecting the environment requires fair public systems as well as responsible actions by individuals, organisations and businesses.",
        "Give one example of an environmental right and one responsibility that helps protect it."
    ),
    "Youth participation in governance": (
        "Youth participation can take place through school councils, community meetings, consultations, youth organisations, civic education and local projects. Young people bring experiences and ideas that can improve decisions affecting education, employment, public spaces and the environment.",
        "Participation is most meaningful when young people receive understandable information, can express views safely and can see how decision-makers respond. Token participation without influence does little to build trust.",
        "Choose one issue affecting young people locally and prepare a clear, respectful question for a community discussion."
    ),
    "Public consultations": (
        "A public consultation is a process through which people can give views on a proposal, policy, project or decision. It may involve meetings, written submissions, surveys or other accessible methods. A useful consultation provides enough information and time for people to respond.",
        "Consultations can reveal concerns that planners have overlooked. They do not require everyone to agree, but decision-makers should consider the feedback and explain how it influenced the decision.",
        "Identify a local development proposal that would benefit from consultation and list the groups who should be heard."
    ),
    "Environmental justice": (
        "Environmental justice examines whether environmental benefits and burdens are distributed fairly and whether affected people can participate in decisions. Some communities may face greater exposure to pollution or have fewer resources to respond to environmental problems.",
        "Fair environmental planning considers who is affected, whose voices are heard and whether solutions create new disadvantages. It also recognises that low-income communities should not be excluded from healthy environments.",
        "Consider a pollution problem and ask which groups experience its effects and whether they have a meaningful voice in decisions."
    ),
    "Community reporting and responsible citizenship": (
        "Responsible reporting gives the relevant organisation clear information about a concern. Useful details may include the type of problem, general location, date and any safe observations. Reports should distinguish what someone has personally observed from what they have heard from others.",
        "Accurate reporting can help authorities or service providers investigate problems. Sharing private information, confronting people or posting unverified accusations online can create additional risks and should be avoided.",
        "Find an appropriate reporting channel for a local environmental concern and note what information it asks residents to provide."
    ),
    "Peaceful dialogue and community problem-solving": (
        "Community disagreements can arise because people have different experiences, priorities and expectations. Peaceful problem-solving involves listening, identifying the actual issue, checking facts, considering different options and agreeing on fair next steps where possible.",
        "Projects are more likely to gain community support when people feel respected. Dialogue does not mean avoiding difficult questions; it means discussing them without intimidation or personal attacks.",
        "Imagine two groups disagree about where a collection point should be placed. Suggest a fair process for hearing both groups."
    ),
    "Can waste become wealth?": (
        "Waste materials can become useful resources when they are collected, sorted and directed to suitable recovery processes. Examples include collecting clean recyclables, repairing discarded products, making items from recovered materials and providing collection services. The quality and condition of materials affect their value.",
        "Waste-based enterprise can create income and local employment, but it needs safe handling, reliable buyers, realistic costs and responsible disposal of materials that cannot be recovered.",
        "Identify one recoverable material in your area and investigate who might collect, process or buy it."
    ),
    "Introduction to entrepreneurship": (
        "Entrepreneurship starts with recognising a need or opportunity and developing a solution. An entrepreneur considers who experiences the problem, what solution might help, what resources are required and whether people will use or pay for the offer.",
        "Entrepreneurship is not only about opening a large company. Small services, cooperatives and community enterprises can address practical needs when they are planned carefully and respond to real demand.",
        "Describe one problem in your community, who experiences it and a simple service or product that could help."
    ),
    "What is a green business?": (
        "A green business provides products or services that reduce environmental harm or support more responsible use of resources. It might focus on repair, recycling, renewable energy, water efficiency, sustainable agriculture or reusable products. A green label alone does not prove that a business is environmentally responsible.",
        "Green businesses need to balance environmental goals with quality, customer needs, fair working conditions and financial sustainability. Their claims should be honest and supported by evidence.",
        "Choose a possible green business and explain what environmental benefit it would provide and how you would check that benefit."
    ),
    "Understanding customers": (
        "Customers are the people or organisations whose needs a business aims to serve. Understanding them involves learning what problem they face, what they currently use, what they value and what prevents them from using a service. Different customers may have different priorities.",
        "A recycling service, for example, may serve households, schools, businesses or organisations. Each group may need different collection times, prices, communication and service arrangements.",
        "Choose a possible EcoLoop-related service and identify two different customer groups and what each might need."
    ),
    "Market research for beginners": (
        "Market research is the process of gathering information about customers, demand, competitors and conditions in a market. Beginners can use simple interviews, observation, short surveys and public information. Questions should be neutral so that people can answer honestly.",
        "Research reduces guesswork, but it cannot guarantee that a business will succeed. Small tests and feedback can help an entrepreneur improve an idea before committing significant resources.",
        "Write three questions you could ask potential customers before starting a recycling or repair service."
    ),
    "Understanding revenue and profit": (
        "Revenue is the income a business receives from selling products or services. Expenses are the costs of operating the business, such as transport, materials, wages and communication. Profit is what remains when relevant expenses are subtracted from revenue. A business can make sales and still make a loss.",
        "Understanding these terms helps entrepreneurs price services, plan spending and decide whether an activity can continue. Good records make it easier to see where money is coming from and where it is going.",
        "Imagine a small collection service. List three possible sources of income or costs it might have."
    ),
    "Building a simple business model": (
        "A business model explains how an organisation creates, delivers and captures value. It identifies the problem being addressed, the customers served, the product or service offered, the resources needed, the main activities and how the venture will earn income or sustain itself.",
        "A simple model helps test whether an idea is practical. It can reveal missing pieces, such as who will pay, how materials will be transported or where recovered items will go.",
        "Describe a simple environmental service using four points: customer, problem, solution and how the service could be sustained."
    ),
    "Cooperatives and collective enterprise": (
        "A cooperative is an organisation owned and democratically controlled by its members to meet shared economic, social or cultural needs. Members contribute to the enterprise and participate in agreed decision-making processes. Clear rules help define responsibilities and how benefits are shared.",
        "People working in waste collection or recycling may be able to pool equipment, knowledge and bargaining power. Cooperation can create opportunities, but it requires trust, record-keeping and fair management.",
        "Identify one resource that members of a waste-collectors' cooperative could share and one rule needed to manage it fairly."
    ),
    "The value of repairing products": (
        "Repair involves restoring an item so it can continue serving its purpose. Repair can require practical skills, tools, spare parts and an understanding of safety. It is not always possible or appropriate, but it can prevent useful products from being discarded too early.",
        "Repair services can support livelihoods and reduce demand for replacement products. They also help preserve the materials and energy already used to make an item.",
        "Choose a common household item and identify what skill or spare part might be needed to repair it safely."
    ),
    "Financial planning for small projects": (
        "A project budget estimates the money and resources needed to carry out planned activities. It should include likely costs, available funds, timing and a small allowance for unexpected expenses where possible. Estimates should be realistic and supported by quotations or research.",
        "A project can have a strong idea but struggle if it cannot afford transport, equipment, communication or maintenance. Tracking actual spending against the budget helps teams make responsible decisions.",
        "Prepare a short list of likely costs for a small community clean-up or recycling activity."
    ),
    "Social entrepreneurship": (
        "Social entrepreneurship applies entrepreneurial thinking to social or environmental problems. The organisation aims to create positive impact while developing a practical way to fund and continue its work. Income may come from sales, service fees, partnerships or a combination of sources.",
        "A social enterprise should be clear about the problem it addresses and how it measures progress. A good intention is not enough; the solution should respond to people's needs and avoid creating new harm.",
        "Identify a social or environmental problem and suggest one service that could address it while remaining financially realistic."
    ),
    "Sustainable business practices": (
        "Sustainable business practices consider how operations affect the environment, workers, customers and the wider community. Examples include reducing unnecessary packaging, using resources efficiently, treating workers fairly and keeping accurate records of environmental claims.",
        "Responsible practices can reduce waste and strengthen long-term relationships with customers and suppliers. Businesses should be honest about what they have achieved and what still needs improvement.",
        "Choose one small business and suggest a realistic improvement to its environmental or social practices."
    ),
    "Technology for a greener future": (
        "Environmental technology includes tools that help people observe, manage or reduce environmental problems. Digital platforms can record waste, map collection points, coordinate volunteers and share educational information. Physical technologies can also support cleaner energy, water management and material recovery.",
        "Technology is useful when it responds to a real need and can be maintained. A complicated tool that people cannot access or understand may be less effective than a simple, reliable solution.",
        "Choose one local environmental challenge and decide whether a digital tool, physical tool or community process would help most."
    ),
    "What is digital innovation?": (
        "Digital innovation means using digital technology to improve a product, service or process. It can involve creating an app, improving how information is shared or making an existing service easier to access. Innovation does not always require inventing new technology.",
        "Successful digital solutions begin with the people who will use them. Designers should understand access to devices, internet connectivity, language, affordability and the skills users already have.",
        "Think of a service in your community that could be easier to access. Describe one small digital improvement."
    ),
    "How QR codes work": (
        "A QR code is a two-dimensional pattern that can store information such as a web address or text. A phone camera or QR reader can scan the pattern and offer to open the linked content. The code itself does not guarantee that the destination is safe or accurate.",
        "Environmental projects can use QR codes on posters, collection points or learning displays. The destination should be checked regularly, and users should be cautious before opening unfamiliar links.",
        "Plan a QR code display for a community learning activity. Decide what information it should open and who will keep that information updated."
    ),
    "Why environmental data matters": (
        "Environmental data is information collected about conditions, activities or changes. A waste project might record material type, weight, collection date and location. Data becomes useful when it is recorded consistently, checked for errors and interpreted in context.",
        "Reliable information can help a project identify busy collection points, monitor participation and understand where services are missing. Data should not be collected simply because technology makes it possible; it should serve a clear purpose.",
        "Choose three pieces of information that would help a community understand its waste collection activities."
    ),
    "Digital literacy": (
        "Digital literacy includes using devices and software, finding information, communicating online, recognising unreliable content and understanding basic digital safety. It also involves knowing when information is missing or when a tool is not suitable for a task.",
        "Digital access and skills differ between people. Good digital projects should use clear language, accessible design and alternatives for people who have limited connectivity or devices.",
        "Identify one digital skill you would like to improve and one safe way to practise it."
    ),
    "Data privacy and online safety": (
        "Personal data can include names, contact details, photographs, account information and precise location information. Responsible digital services collect only what they need, explain why it is collected and limit who can access it. Strong passwords and careful sharing also help protect users.",
        "Community platforms should not expose members' private information unnecessarily. Before sharing a photograph, location or personal detail, consider whether the person has agreed and whether the information is needed.",
        "Review an app or website you use. Identify one privacy setting or safety practice that helps protect your information."
    ),
    "Citizen science": (
        "Citizen science involves members of the public contributing observations or data to a research activity. Participants may record rainfall, observe birds, report litter or monitor changes in local environments. Clear instructions help make observations more consistent.",
        "Community contributions can expand the information available to researchers and local organisations. Data quality still matters: participants should record what they actually observe and avoid guessing.",
        "Suggest one environmental observation that residents could record regularly using a simple, consistent method."
    ),
    "Environmental storytelling": (
        "Environmental storytelling uses words, photographs, video, music or other creative formats to explain environmental experiences. A strong story gives context, shows why an issue matters and helps an audience understand the people or ecosystems affected.",
        "Stories can make technical issues more relatable, but they should be accurate and respectful. People should not be photographed or identified in sensitive situations without appropriate permission.",
        "Outline a short story about a local environmental issue. Include the place, the challenge and a possible community response."
    ),
    "Media literacy and misinformation": (
        "Media literacy is the ability to access, analyse and evaluate information across different media. A claim may be misleading because it uses an old image, removes important context, exaggerates a finding or comes from an unreliable source.",
        "Before sharing an environmental claim, check who published it, when it was published, what evidence is provided and whether other reliable sources support it. A confident headline is not proof.",
        "Choose a claim you have seen online and list the checks you would make before sharing it."
    ),
    "Introduction to artificial intelligence": (
        "Artificial intelligence refers to computer systems designed to perform tasks such as recognising patterns, processing language, generating content or making predictions. Different AI systems work in different ways, and their outputs can contain errors or reflect bias in their data.",
        "AI may help organise environmental information or support analysis, but people remain responsible for checking results. Sensitive decisions should not rely on an AI output without suitable human review.",
        "Suggest one low-risk way AI could support an environmental project and explain how a person would check its output."
    ),
    "Mapping technology for communities": (
        "Mapping tools represent places and features geographically. A community map might show recycling points, public facilities, drainage concerns or areas where services are limited. Maps can combine observations with other information to support planning.",
        "Maps can help people see patterns that are difficult to understand from lists alone. However, location information can be sensitive, so exact household locations or personal movements should not be shared without a clear need and proper safeguards.",
        "Choose one type of environmental service that would be useful to show on a community map."
    ),
    "Design thinking and problem-solving": (
        "Design thinking is a human-centred approach to solving problems. It often involves understanding people's experiences, defining the problem, generating ideas, making a simple prototype, testing it and improving it. Feedback is used to learn, not merely to seek praise.",
        "A solution may look impressive but still fail if it does not fit people's needs. Early testing with users can reveal confusion, access barriers and practical problems before more resources are invested.",
        "Choose a problem an app could address. Identify one person you would consult and one question you would ask before designing it."
    ),
    "Arts, creativity and climate action": (
        "Creative work can communicate environmental issues through music, theatre, visual arts, photography, storytelling and design. Art can help people connect information to local experiences and imagine different futures. It can also create opportunities for young people to contribute their skills.",
        "Creative campaigns are strongest when they are inclusive, factually responsible and connected to a practical action. A message should invite participation rather than shame or mislead its audience.",
        "Design a simple creative campaign for responsible waste management. Choose an audience, a message and a suitable creative format."
    )
}


LESSONS = []

for index, item in enumerate(READING_TOPICS, start=1):
    title, category, description, original_content, action = item

    extra_content, local_relevance, practical_action = LESSON_DETAILS.get(
        title,
        (
            original_content,
            description,
            action
        )
    )

    LESSONS.append({
        "id": f"eco_{index:03d}",
        "title": title,
        "category": category,
        "pillar": category,
        "minutes": 4,
        "description": description,
        "content": [
            ("Understanding the topic", original_content + "\n\n" + extra_content),
            ("Why it matters", local_relevance),
            ("Put it into practice", practical_action)
        ],
        "action": practical_action
    })


# ============================================================
# 2. ORIGINAL QUIZ QUESTION BANK — 50 QUESTIONS
# Preserved for the separate Eco Quizzes Quiz Centre.
# ============================================================

RAW_QUESTIONS = [
    ("Climate Action & Environment", "Beginner", "What can happen when waste blocks drainage systems?", ["It can contribute to flooding", "It improves water quality", "It creates more drainage space", "It makes waste disappear"], 0, "Blocked drains prevent water from flowing properly."),
    ("Climate Action & Environment", "Beginner", "Which material can commonly be recycled?", ["Clean paper", "Dirty wastewater", "Chemical waste", "Contaminated medical waste"], 0, "Clean paper can be processed into new paper products."),
    ("Climate Action & Environment", "Beginner", "What is biodiversity?", ["The variety of living organisms", "The number of buildings", "The amount of plastic", "The study of machines"], 0, "Biodiversity includes the variety of living organisms."),
    ("Climate Action & Environment", "Intermediate", "Which activity contributes directly to human-caused climate change?", ["Burning fossil fuels", "Separating recyclables", "Planting trees", "Collecting rainwater"], 0, "Burning fossil fuels releases greenhouse gases."),
    ("Climate Action & Environment", "Beginner", "What are the 3Rs?", ["Reduce, Reuse, Recycle", "Remove, Replace, Repair", "Reuse, Remove, Release", "Recover, Reject, Rebuild"], 0, "The 3Rs encourage waste prevention and recovery."),
    ("Climate Action & Environment", "Intermediate", "Why are wetlands important?", ["They regulate water and support wildlife", "They increase plastic pollution", "They prevent all rainfall", "They eliminate clean water needs"], 0, "Wetlands support biodiversity and water regulation."),
    ("Climate Action & Environment", "Intermediate", "Why separate waste at source?", ["To make recovery and recycling easier", "To increase mixed waste", "To make materials hazardous", "To prevent collection"], 0, "Separation makes recovery easier."),
    ("Climate Action & Environment", "Beginner", "Which energy source is renewable?", ["Solar energy", "Coal", "Diesel", "Petrol"], 0, "Solar energy comes from sunlight."),
    ("Climate Action & Environment", "Intermediate", "How can indigenous trees benefit Zimbabwe?", ["Support biodiversity and ecosystems", "Increase soil erosion", "Eliminate all insects", "Reduce oxygen"], 0, "Indigenous trees support local ecosystems."),
    ("Climate Action & Environment", "Advanced", "What is climate adaptation?", ["Adjusting to climate impacts", "Stopping all weather changes", "Increasing fossil fuel use", "Ignoring climate risks"], 0, "Adaptation helps communities prepare for climate impacts."),
    ("Climate Action & Environment", "Intermediate", "Why handle electronic waste carefully?", ["It may contain hazardous substances", "It decomposes within days", "It is safe to burn", "It has no reusable materials"], 0, "Electronic waste can contain hazardous substances."),
    ("Climate Action & Environment", "Advanced", "What is the difference between mitigation and adaptation?", ["Mitigation reduces causes; adaptation manages impacts", "Both increase pollution", "They mean exactly the same thing", "Neither relates to climate"], 0, "Mitigation addresses causes; adaptation addresses impacts."),
    ("Climate Action & Environment", "Advanced", "What is a circular economy?", ["Keeping materials and products in use longer", "An economy based on dumping", "Using every product once", "Discouraging repairs"], 0, "Circular systems reduce waste through reuse and recovery."),

    ("Governance & Civic Education", "Beginner", "Who has a role in keeping communities clean?", ["Only government", "Only schools", "Only collectors", "Individuals, communities, businesses and institutions"], 3, "Environmental responsibility is shared."),
    ("Governance & Civic Education", "Beginner", "What is civic responsibility?", ["Contributing positively to society", "Ignoring community problems", "Avoiding public discussion", "Leaving all responsibility to businesses"], 0, "Civic responsibility involves contributing to society."),
    ("Governance & Civic Education", "Intermediate", "Why should communities participate in local decisions?", ["They understand local needs", "They replace every institution", "They should silence others", "They have no role"], 0, "Participation helps decisions reflect people's needs."),
    ("Governance & Civic Education", "Intermediate", "What is accountability?", ["Leaders being answerable for actions", "Leaders avoiding questions", "Keeping all decisions secret", "Allowing pollution without consequences"], 0, "Accountability requires decision-makers to take responsibility."),
    ("Governance & Civic Education", "Beginner", "Why report illegal dumping?", ["To help address environmental problems", "To encourage dumping", "To hide pollution", "To prevent monitoring"], 0, "Reporting helps identify environmental violations."),
    ("Governance & Civic Education", "Advanced", "What does environmental justice focus on?", ["Fair treatment and meaningful participation", "Protection only for wealthy areas", "Ignoring disadvantaged areas", "Removing communities from decisions"], 0, "Environmental justice concerns fairness."),
    ("Governance & Civic Education", "Intermediate", "Why are public consultations important?", ["They allow affected people to contribute", "They prevent questions", "They guarantee agreement", "They remove transparency"], 0, "Consultations give people an opportunity to express views."),
    ("Governance & Civic Education", "Beginner", "Which action demonstrates environmental citizenship?", ["Joining a community clean-up", "Dumping rubbish in a river", "Damaging public trees", "Encouraging pollution"], 0, "Environmental citizenship involves responsible action."),
    ("Governance & Civic Education", "Advanced", "Why is transparency important in waste programmes?", ["It helps people understand decisions and resource use", "It prevents monitoring", "It removes reporting", "It hides public spending"], 0, "Transparency supports public trust."),
    ("Governance & Civic Education", "Intermediate", "What is a role of local authorities in waste management?", ["Supporting services and environmental management", "Encouraging illegal dumping", "Preventing recycling", "Removing participation"], 0, "Local authorities support public services."),
    ("Governance & Civic Education", "Advanced", "What is participatory governance?", ["Involving citizens in decisions affecting them", "One leader making every decision", "Preventing public access to information", "Ignoring affected people"], 0, "Participatory governance includes citizens."),
    ("Governance & Civic Education", "Intermediate", "Why should environmental information be accessible to young people?", ["It supports informed participation", "It prevents questions", "It makes action unnecessary", "It discourages education"], 0, "Reliable information supports responsible participation."),

    ("Business & Entrepreneurship", "Beginner", "Which is an example of a green business?", ["Illegal dumping", "Collecting recyclable materials", "Burning waste", "Throwing reusable items away"], 1, "Recycling collection can create value and reduce waste."),
    ("Business & Entrepreneurship", "Beginner", "What is entrepreneurship?", ["Identifying opportunities and creating ventures", "Avoiding every opportunity", "Copying without research", "Waiting for others"], 0, "Entrepreneurship involves creating value."),
    ("Business & Entrepreneurship", "Intermediate", "How can recycling create employment?", ["Collection, sorting, processing and sales", "Eliminating business activity", "Preventing repairs", "Making materials unusable"], 0, "Different stages can support jobs."),
    ("Business & Entrepreneurship", "Beginner", "What is a business customer?", ["A person or organisation buying a product or service", "Someone who never uses products", "Only the owner", "A regulation"], 0, "Customers are those whose needs a business serves."),
    ("Business & Entrepreneurship", "Intermediate", "What is a value proposition?", ["The value a product or service offers", "The owner's biography", "Unrelated expenses", "Competitors' addresses"], 0, "It explains why customers might choose an offer."),
    ("Business & Entrepreneurship", "Intermediate", "Why conduct market research?", ["To understand needs, demand and competitors", "To guarantee profit", "To remove all risks", "To avoid planning"], 0, "Research helps entrepreneurs understand the market."),
    ("Business & Entrepreneurship", "Beginner", "What is revenue?", ["Money earned from sales", "Number of employees", "Amount of waste", "Business expenses"], 0, "Revenue is income generated through sales."),
    ("Business & Entrepreneurship", "Advanced", "What is profit?", ["Revenue remaining after expenses", "The number of customers", "All unpaid invoices", "The total number of products"], 0, "Profit is calculated after costs are deducted."),
    ("Business & Entrepreneurship", "Intermediate", "What is one benefit of a cooperative?", ["Members pool resources and negotiate collectively", "Members never communicate", "Members cannot share information", "No responsibilities are needed"], 0, "Cooperatives support collective action."),
    ("Business & Entrepreneurship", "Advanced", "What does a sustainable business model aim to achieve?", ["Long-term economic viability with social and environmental consideration", "Sales regardless of harm", "Growth without customers", "Unlimited resource waste"], 0, "Sustainability considers economic, social and environmental effects."),
    ("Business & Entrepreneurship", "Intermediate", "Why can repairing products support a circular economy?", ["It extends product life", "It guarantees waste", "It increases unnecessary disposal", "It prevents reuse"], 0, "Repair keeps products useful for longer."),
    ("Business & Entrepreneurship", "Advanced", "What is the break-even point?", ["Revenue equals total costs", "A business has no customers", "Expenses are zero", "Sales are not recorded"], 0, "At break-even, revenue covers costs."),

    ("Technology, Innovation, Media & Arts", "Beginner", "How can technology support environmental protection?", ["Monitoring and organising waste collection", "Encouraging dumping", "Preventing information sharing", "Making recycling impossible"], 0, "Digital tools can support environmental coordination."),
    ("Technology, Innovation, Media & Arts", "Beginner", "What is digital innovation?", ["Using digital technology in new or improved ways", "Avoiding technology", "Decoration only", "Preventing information sharing"], 0, "Digital innovation improves products and processes."),
    ("Technology, Innovation, Media & Arts", "Intermediate", "How can QR codes help an environmental project?", ["Linking users to digital information", "Automatically removing waste", "Replacing education", "Blocking websites"], 0, "QR codes provide quick access to information."),
    ("Technology, Innovation, Media & Arts", "Intermediate", "Why collect data in a waste-management app?", ["To track activities and support decisions", "To make reports inaccurate", "To hide progress", "To remove verification"], 0, "Reliable data supports better decisions."),
    ("Technology, Innovation, Media & Arts", "Beginner", "What is digital literacy?", ["Using digital tools and information responsibly", "Operating one phone only", "Avoiding all information", "Creating passwords for others"], 0, "Digital literacy includes responsible technology use."),
    ("Technology, Innovation, Media & Arts", "Advanced", "Why is data verification important?", ["It helps make information accurate and trustworthy", "It guarantees every claim", "It makes evidence unnecessary", "It protects incorrect records"], 0, "Verification helps identify errors."),
    ("Technology, Innovation, Media & Arts", "Intermediate", "What is citizen science?", ["Public participation in research and data collection", "Research only by companies", "Preventing public observations", "Technology without information"], 0, "The public can contribute observations to research."),
    ("Technology, Innovation, Media & Arts", "Beginner", "How can environmental storytelling help?", ["Making issues understandable through stories", "Hiding problems", "Discouraging awareness", "Replacing evidence with rumours"], 0, "Stories can make issues relatable."),
    ("Technology, Innovation, Media & Arts", "Intermediate", "What should you do before sharing an environmental claim?", ["Check reliable sources", "Share immediately", "Remove the source", "Change the facts"], 0, "Checking sources reduces misinformation."),
    ("Technology, Innovation, Media & Arts", "Advanced", "What is artificial intelligence?", ["Computer systems performing tasks requiring human-like intelligence", "A machine that is always perfect", "Renewable energy", "A system without data"], 0, "AI systems perform tasks such as pattern recognition."),
    ("Technology, Innovation, Media & Arts", "Advanced", "How can mapping help waste management?", ["Identifying collection points and service gaps", "Making locations impossible to identify", "Preventing route planning", "Removing participation"], 0, "Mapping helps visualise locations and service needs."),
    ("Technology, Innovation, Media & Arts", "Intermediate", "Why is user feedback important in app design?", ["It helps improve the app for users", "It guarantees perfection", "It removes testing", "It prevents problem reports"], 0, "Feedback identifies problems and improvements."),
    ("Technology, Innovation, Media & Arts", "Advanced", "What is an important responsibility when collecting user data?", ["Protecting personal information", "Publishing private information", "Collecting unnecessary information", "Sharing passwords"], 0, "Responsible data practices protect privacy.")
]


QUIZ_QUESTIONS = [
    {
        "category": q[0],
        "difficulty": q[1],
        "question": q[2],
        "options": q[3],
        "answer": q[4],
        "explanation": q[5]
    }
    for q in RAW_QUESTIONS
]


# ============================================================
# 3. TIME DISPLAY
# ============================================================

def _format_member_time(timestamp, timezone_name=None):
    if not timestamp:
        return "Time unavailable"

    try:
        value = datetime.fromisoformat(
            str(timestamp).replace("Z", "+00:00")
        )

        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)

        if timezone_name:
            try:
                value = value.astimezone(ZoneInfo(timezone_name))
            except (ZoneInfoNotFoundError, ValueError):
                value = value.astimezone(timezone.utc)
        else:
            value = value.astimezone(timezone.utc)

        return value.strftime("%d %b %Y · %I:%M %p")

    except Exception:
        return str(timestamp)


# ============================================================
# 4. GENERAL HELPERS
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

    except Exception:
        return []


def _comments_section(
    supabase,
    user_id,
    content_type,
    content_id,
    user_name,
    group_name=None,
    timezone_name=None
):
    st.markdown("#### 💬 Community discussion")

    comments = _load_comments(
        supabase,
        content_type,
        content_id
    )

    if comments:
        for comment in comments:
            with st.container(border=True):
                display_name = _safe_name(
                    comment.get("full_name")
                )

                if comment.get("group_name"):
                    display_name += (
                        f" · {comment['group_name']}"
                    )

                st.markdown(f"**{display_name}**")
                st.write(comment.get("comment", ""))

                st.caption(
                    _format_member_time(
                        comment.get("created_at"),
                        timezone_name
                    )
                )
    else:
        st.caption(
            "No comments yet. Start the conversation!"
        )

    comment_text = st.text_area(
        "Share your thoughts",
        key=f"comment_{content_type}_{content_id}",
        max_chars=1000
    )

    if st.button(
        "Post comment",
        key=f"post_{content_type}_{content_id}",
        use_container_width=True
    ):
        if not user_id:
            st.error("Please sign in to comment.")
            return

        if not comment_text.strip():
            st.warning("Please write a comment first.")
            return

        payload = {
            "user_id": user_id,
            "full_name": user_name,
            "content_type": content_type,
            "content_id": str(content_id),
            "comment": comment_text.strip()
        }

        if group_name:
            payload["group_name"] = group_name

        try:
            supabase.table(
                "learning_comments"
            ).insert(payload).execute()

            st.success("Your comment has been shared!")
            st.rerun()

        except Exception as e:
            if "group_name" in str(e).lower():
                payload.pop("group_name", None)

                try:
                    supabase.table(
                        "learning_comments"
                    ).insert(payload).execute()

                    st.success(
                        "Your comment has been shared!"
                    )
                    st.rerun()

                except Exception as retry_error:
                    st.error(
                        f"Could not post comment: {retry_error}"
                    )
            else:
                st.error(f"Could not post comment: {e}")


def _get_approved_groups(supabase, user_id):
    if not user_id:
        return []

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

        if not group_ids:
            return []

        response = (
            supabase.table("community_groups")
            .select("*")
            .in_("id", group_ids)
            .execute()
        )

        return response.data or []

    except Exception as e:
        st.warning(f"Could not load approved groups: {e}")
        return []


def _group_selector(supabase, user_id, user_name, key):
    groups = _get_approved_groups(supabase, user_id)
    choices = [None] + groups

    selected = st.selectbox(
        "Where should this activity count?",
        choices,
        format_func=lambda g: (
            f"{user_name} (Individual)"
            if g is None
            else (
                g.get("group_name")
                or g.get("name")
                or g.get("title")
                or "Community Group"
            )
        ),
        key=key
    )

    if selected is None:
        return None, None

    group_name = (
        selected.get("group_name")
        or selected.get("name")
        or selected.get("title")
        or "Community Group"
    )

    return selected.get("id"), group_name


# ============================================================
# 5. DISCOVER & LEARN
# ============================================================

def _reading_library(
    supabase,
    user_id,
    group_id,
    user_name,
    timezone_name=None
):
    st.subheader("📚 Discover & Learn")

    st.write(
        "Explore 50 learning materials across all four "
        "NGIH pillars. Build knowledge, connect ideas "
        "to community challenges and take practical action."
    )

    activity_group_id, activity_group_name = _group_selector(
        supabase,
        user_id,
        user_name,
        "learning_group_choice"
    )

    selected_id = st.session_state.get(
        "selected_learning_lesson"
    )

    # --------------------------------------------------------
    # OPEN LESSON VIEW
    # --------------------------------------------------------

    if selected_id:
        lesson = next(
            (
                item for item in LESSONS
                if item["id"] == selected_id
            ),
            None
        )

        if lesson:
            st.button(
                "← Back to learning library",
                key="back_lessons",
                on_click=lambda: st.session_state.pop(
                    "selected_learning_lesson",
                    None
                )
            )

            st.divider()
            st.markdown(f"## {lesson['title']}")

            st.caption(
                f"{lesson['category']} · "
                f"{lesson['minutes']} minute read"
            )

            for heading, paragraph in lesson["content"]:
                st.markdown(f"### {heading}")
                st.write(paragraph)

            st.info(
                f"🌱 **Your action:** {lesson['action']}"
            )

            if st.button(
                "✅ Mark lesson as completed",
                key=f"complete_{lesson['id']}",
                use_container_width=True
            ):
                if not user_id:
                    st.error(
                        "Please sign in to record your progress."
                    )
                else:
                    try:
                        check = (
                            supabase.table("learning_completions")
                            .select("id")
                            .eq("user_id", user_id)
                            .eq("lesson_id", lesson["id"])
                        )

                        if activity_group_id:
                            check = check.eq(
                                "group_id",
                                activity_group_id
                            )
                        else:
                            check = check.is_(
                                "group_id",
                                "null"
                            )

                        previous = check.limit(1).execute()

                        if previous.data:
                            st.info(
                                "This lesson is already completed "
                                "for this account."
                            )
                        else:
                            # The existing database points trigger
                            # handles learning points. Do not insert
                            # another point transaction here.
                            supabase.table(
                                "learning_completions"
                            ).insert({
                                "user_id": user_id,
                                "group_id": activity_group_id,
                                "lesson_id": lesson["id"]
                            }).execute()

                            st.success(
                                "Lesson completion recorded! "
                                "Your learning points are processed "
                                "through EcoLoop's points system."
                            )

                            st.rerun()

                    except Exception as e:
                        st.error(
                            f"Could not record completion: {e}"
                        )

            _comments_section(
                supabase,
                user_id,
                "lesson",
                lesson["id"],
                user_name,
                activity_group_name,
                timezone_name
            )

        else:
            st.warning(
                "That learning material could not be found."
            )
            st.session_state.pop(
                "selected_learning_lesson",
                None
            )

        return

    # --------------------------------------------------------
    # LIBRARY VIEW
    # --------------------------------------------------------

    categories = ["All categories"] + PILLARS

    selected_category = st.selectbox(
        "Explore a learning area",
        categories,
        key="learning_category"
    )

    search = st.text_input(
        "Search learning materials",
        placeholder="Search by topic..."
    )

    lessons = LESSONS

    if selected_category != "All categories":
        lessons = [
            lesson for lesson in lessons
            if lesson["category"] == selected_category
        ]

    if search.strip():
        search_term = search.strip().lower()

        lessons = [
            lesson for lesson in lessons
            if search_term in (
                lesson["title"] + " "
                + lesson["description"] + " "
                + lesson["category"]
            ).lower()
        ]

    st.caption(
        f"{len(lessons)} learning materials available"
    )

    # Reset pagination when the search or category changes.
    filter_signature = (
        selected_category + "|" + search.strip().lower()
    )

    if st.session_state.get(
        "learning_filter_signature"
    ) != filter_signature:
        st.session_state["learning_filter_signature"] = (
            filter_signature
        )
        st.session_state["learning_library_page"] = 1

    page_size = 10
    total_pages = max(
        1,
        (len(lessons) + page_size - 1) // page_size
    )

    page_key = "learning_library_page"

    if page_key not in st.session_state:
        st.session_state[page_key] = 1

    if st.session_state[page_key] > total_pages:
        st.session_state[page_key] = 1

    current_page = st.session_state[page_key]

    start_index = (current_page - 1) * page_size
    end_index = start_index + page_size

    visible_lessons = lessons[start_index:end_index]

    if not visible_lessons:
        st.info(
            "No learning materials match your search."
        )
        return

    for lesson in visible_lessons:
        with st.container(border=True):
            st.markdown(f"### {lesson['title']}")

            st.caption(
                f"{lesson['category']} · "
                f"{lesson['minutes']} minute read"
            )

            st.write(lesson["description"])

            if st.button(
                "Read lesson",
                key=f"read_{lesson['id']}",
                use_container_width=True
            ):
                st.session_state[
                    "selected_learning_lesson"
                ] = lesson["id"]

                st.rerun()

    st.divider()

    st.caption(
        f"Page {current_page} of {total_pages}"
    )

    previous_col, page_col, next_col = st.columns(
        [1, 2, 1]
    )

    with previous_col:
        if st.button(
            "← Previous",
            disabled=current_page <= 1,
            use_container_width=True
        ):
            st.session_state[page_key] -= 1
            st.rerun()

    with page_col:
        st.markdown(
            f"<div style='text-align:center;padding-top:8px'>"
            f"Showing {start_index + 1}–"
            f"{min(end_index, len(lessons))} of {len(lessons)}"
            f"</div>",
            unsafe_allow_html=True
        )

    with next_col:
        if st.button(
            "Next →",
            disabled=current_page >= total_pages,
            use_container_width=True
        ):
            st.session_state[page_key] += 1
            st.rerun()


# ============================================================
# 6. ORIGINAL QUIZ FUNCTION
# Kept available for compatibility, but NOT displayed as a
# tab inside Explore & Learn.
# ============================================================

def _quiz_centre(
    supabase,
    user_id,
    group_id,
    user_name
):
    st.subheader("🧠 Knowledge Challenge")

    st.write(
        "Test your knowledge across all four NGIH pillars."
    )

    quiz_group_id, quiz_group_name = _group_selector(
        supabase,
        user_id,
        user_name,
        "quiz_group_choice"
    )

    st.caption(
        f"{len(QUIZ_QUESTIONS)} questions · "
        "1 point for each correct answer"
    )

    if "explore_quiz_answers" not in st.session_state:
        st.session_state["explore_quiz_answers"] = {}

    if "explore_quiz_submitted" not in st.session_state:
        st.session_state["explore_quiz_submitted"] = False

    answers = st.session_state["explore_quiz_answers"]

    for index, question in enumerate(QUIZ_QUESTIONS):
        st.markdown(
            f"**Question {index + 1} of "
            f"{len(QUIZ_QUESTIONS)}**"
        )

        st.caption(
            f"{question['category']} · "
            f"{question['difficulty']}"
        )

        st.write(question["question"])

        selected = st.radio(
            "Choose your answer:",
            question["options"],
            index=None,
            key=f"explore_answer_{index}",
            disabled=st.session_state[
                "explore_quiz_submitted"
            ],
            label_visibility="collapsed"
        )

        if selected is not None:
            answers[index] = question["options"].index(
                selected
            )

        if st.session_state["explore_quiz_submitted"]:
            correct = question["answer"]

            if answers.get(index) == correct:
                st.success(
                    "Correct! " + question["explanation"]
                )
            else:
                st.error(
                    "Not quite. " + question["explanation"]
                )

        st.divider()

    if not st.session_state["explore_quiz_submitted"]:
        if st.button(
            "Submit my answers",
            use_container_width=True
        ):
            if len(answers) != len(QUIZ_QUESTIONS):
                st.warning(
                    "Please answer all questions first."
                )
            else:
                score = sum(
                    1
                    for index, question in enumerate(
                        QUIZ_QUESTIONS
                    )
                    if answers.get(index) == question["answer"]
                )

                st.session_state[
                    "explore_quiz_score"
                ] = score

                st.session_state[
                    "explore_quiz_submitted"
                ] = True

                if user_id:
                    try:
                        # Save the attempt. The existing points
                        # system should handle quiz scoring.
                        # Do not manually add another point
                        # transaction here.
                        supabase.table(
                            "quiz_attempts"
                        ).insert({
                            "user_id": user_id,
                            "quiz_id": "explore_learn_50",
                            "group_id": quiz_group_id,
                            "score": score,
                            "total_questions": len(QUIZ_QUESTIONS),
                            "completed_at": datetime.now(
                                timezone.utc
                            ).isoformat()
                        }).execute()

                    except Exception as e:
                        st.warning(
                            "Your result is calculated, but the "
                            f"attempt could not be fully saved: {e}"
                        )
                else:
                    st.info(
                        "Sign in to save your quiz result "
                        "and earn points."
                    )

                st.rerun()

    else:
        score = st.session_state.get(
            "explore_quiz_score",
            0
        )

        st.markdown("### Your results")

        st.metric(
            "Your score",
            f"{score} / {len(QUIZ_QUESTIONS)}"
        )

        st.metric(
            "Points earned",
            score if user_id else 0
        )

        if score == len(QUIZ_QUESTIONS):
            st.success(
                "Outstanding! You got every question right."
            )
        elif score >= 30:
            st.success(
                "Excellent work! Keep building your knowledge."
            )
        elif score >= 20:
            st.success("Good work! Keep learning.")
        else:
            st.info(
                "Keep learning. You can improve with practice."
            )

        if st.button(
            "Try the quiz again",
            use_container_width=True
        ):
            st.session_state[
                "explore_quiz_answers"
            ] = {}

            st.session_state[
                "explore_quiz_submitted"
            ] = False

            st.session_state.pop(
                "explore_quiz_score",
                None
            )

            for index in range(len(QUIZ_QUESTIONS)):
                st.session_state.pop(
                    f"explore_answer_{index}",
                    None
                )

            st.rerun()


# ============================================================
# 7. RESOURCE LIBRARY AND MEMBER UPLOADS
# ============================================================

def _resource_library(
    supabase,
    user_id,
    is_coordinator
):
    st.subheader("🌍 Reading & Resource Library")

    st.write(
        "Explore approved learning materials shared "
        "by the EcoLoop community."
    )

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
        st.error(
            f"Could not load the resource library: {e}"
        )

    if resources:
        for resource in resources:
            with st.container(border=True):
                st.markdown(
                    f"### 📖 "
                    f"{resource.get('title', 'Learning resource')}"
                )

                st.caption(
                    resource.get("category", "General")
                )

                st.write(
                    resource.get("description", "")
                )

                file_path = resource.get("file_path")

                if file_path:
                    try:
                        pdf_bytes = (
                            supabase.storage
                            .from_("learning-resources")
                            .download(file_path)
                        )

                        st.download_button(
                            "⬇️ Download PDF",
                            data=pdf_bytes,
                            file_name=(
                                resource.get(
                                    "title",
                                    "EcoLoop resource"
                                ).replace("/", "-") + ".pdf"
                            ),
                            mime="application/pdf",
                            key=(
                                f"download_resource_"
                                f"{resource['id']}"
                            ),
                            use_container_width=True
                        )

                    except Exception:
                        st.warning(
                            "This PDF could not be downloaded."
                        )

                if resource.get("resource_url"):
                    st.link_button(
                        "🔗 Open online resource",
                        resource["resource_url"],
                        use_container_width=True
                    )

                if resource.get("licence"):
                    st.caption(
                        f"Licence: {resource['licence']}"
                    )

    else:
        st.info(
            "The approved resource library is currently growing."
        )

    st.divider()

    st.markdown("### 📤 Contribute a learning resource")

    with st.form(
        "learning_resource_upload",
        clear_on_submit=True
    ):
        title = st.text_input("Resource title")

        description = st.text_area(
            "What will people learn?"
        )

        category = st.selectbox(
            "Learning category",
            PILLARS
        )

        licence = st.text_input(
            "Copyright / licence information"
        )

        resource_url = st.text_input(
            "Resource link (optional)",
            placeholder="https://..."
        )

        uploaded_file = st.file_uploader(
            "Upload a PDF (optional)",
            type=["pdf"]
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
                    "Please provide copyright or licence information."
                )

            elif not resource_url.strip() and uploaded_file is None:
                st.warning(
                    "Please provide a link or upload a PDF."
                )

            else:
                file_path = None

                try:
                    if uploaded_file is not None:
                        file_path = (
                            f"{user_id}/"
                            f"{uuid.uuid4().hex}_"
                            f"{uploaded_file.name}"
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

                    supabase.table(
                        "learning_resources"
                    ).insert({
                        "title": title.strip(),
                        "description": description.strip(),
                        "category": category,
                        "licence": licence.strip(),
                        "resource_url": (
                            resource_url.strip() or None
                        ),
                        "file_path": file_path,
                        "submitted_by": user_id,
                        "status": "pending"
                    }).execute()

                    st.success(
                        "Resource submitted for coordinator approval!"
                    )

                    st.rerun()

                except Exception as e:
                    st.error(
                        f"Resource submission failed: {e}"
                    )


# ============================================================
# 8. COORDINATOR RESOURCE APPROVAL
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
        st.error(
            f"Could not load pending resources: {e}"
        )
        return

    if not pending:
        st.success(
            "There are no resources waiting for approval."
        )
        return

    for resource in pending:
        with st.container(border=True):
            st.markdown(
                f"### {resource.get('title')}"
            )

            st.write(
                resource.get("description", "")
            )

            st.caption(
                f"{resource.get('category')} · "
                f"Licence: {resource.get('licence')}"
            )

            if resource.get("resource_url"):
                st.link_button(
                    "Review resource",
                    resource["resource_url"]
                )

            if resource.get("file_path"):
                try:
                    pdf_bytes = (
                        supabase.storage
                        .from_("learning-resources")
                        .download(resource["file_path"])
                    )

                    st.download_button(
                        "Download submitted PDF for review",
                        data=pdf_bytes,
                        file_name="submitted_resource.pdf",
                        mime="application/pdf",
                        key=f"review_pdf_{resource['id']}"
                    )

                except Exception:
                    st.warning(
                        "The submitted PDF could not be retrieved."
                    )

            col1, col2 = st.columns(2)

            with col1:
                if st.button(
                    "Approve",
                    key=f"approve_resource_{resource['id']}",
                    use_container_width=True
                ):
                    try:
                        supabase.table(
                            "learning_resources"
                        ).update({
                            "status": "approved"
                        }).eq(
                            "id",
                            resource["id"]
                        ).execute()

                        st.success("Resource approved.")
                        st.rerun()

                    except Exception as e:
                        st.error(
                            f"Approval failed: {e}"
                        )

            with col2:
                if st.button(
                    "Reject",
                    key=f"reject_resource_{resource['id']}",
                    use_container_width=True
                ):
                    try:
                        supabase.table(
                            "learning_resources"
                        ).update({
                            "status": "rejected"
                        }).eq(
                            "id",
                            resource["id"]
                        ).execute()

                        st.warning("Resource rejected.")
                        st.rerun()

                    except Exception as e:
                        st.error(
                            f"Rejection failed: {e}"
                        )


# ============================================================
# 9. MAIN EXPLORE & LEARN PAGE
# ============================================================

def render_explore_learn(
    supabase,
    user_id=None,
    user_name="EcoLoop Member",
    group_id=None,
    is_coordinator=False,
    role=None,
    timezone_name=None
):
    st.title("📚 Explore & Learn")

    st.write(
        "Learn something useful. Understand why it matters. "
        "Do something with that knowledge."
    )

    st.info(
        "🌱 Explore knowledge, discover new ideas, "
        "build practical skills and share what you know."
    )

    privileged_roles = {
        "coordinator",
        "admin",
        "super_admin",
        "super admin"
    }

    role_name = str(role or "").strip().lower()

    coordinator_access = (
        bool(is_coordinator)
        or role_name in privileged_roles
    )

    # Explore & Learn has only two sections.
    # The separate Eco Quizzes Quiz Centre keeps its own route.
    tabs = st.tabs([
        "📚 Discover",
        "🌍 Resource Library"
    ])

    with tabs[0]:
        _reading_library(
            supabase,
            user_id,
            group_id,
            user_name,
            timezone_name
        )

    with tabs[1]:
        _resource_library(
            supabase,
            user_id,
            coordinator_access
        )

    if coordinator_access:
        st.divider()

        with st.expander(
            "🛡️ Coordinator Tools",
            expanded=False
        ):
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
