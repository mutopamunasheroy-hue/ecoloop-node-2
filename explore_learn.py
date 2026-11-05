# ============================================================
# ECOLOOP NODE — EXPLORE & LEARN
# Powered by Next Gen Impact Hub (NGIH)
# Global learning with relevant local perspectives
# ============================================================

import streamlit as st
import uuid
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


# ============================================================
# 1. NGIH PILLARS
# ============================================================

PILLARS = [
    "Climate Action & Environment",
    "Governance & Civic Education",
    "Business & Entrepreneurship",
    "Technology, Innovation, Media & Arts"
]


# ============================================================
# 2. EXPANDED LEARNING MATERIALS — LESSONS 1–25
# Each lesson includes:
# Core knowledge, deeper explanation, global perspective,
# development relevance and a practical action.
# ============================================================

READING_TOPICS = [

    # --------------------------------------------------------
    # CLIMATE ACTION & ENVIRONMENT — 1 TO 13
    # --------------------------------------------------------

    {
        "title": "Where does our waste go?",
        "pillar": PILLARS[0],
        "description": "Follow the journey of waste and understand what happens when disposal systems fail.",
        "minutes": 6,
        "content": [
            ("Understanding the waste journey",
             "Waste does not simply disappear when it leaves a household, school or business. It enters a chain of activities that may include collection, transportation, sorting, recycling, treatment and final disposal. The route depends on the material, the local infrastructure and the waste-management system available. When collection systems are unreliable, waste may accumulate in streets, vacant land, waterways and informal dumping areas."),
            ("What happens when waste is mismanaged?",
             "Uncollected waste can block storm-water drains, contribute to flooding, attract pests and contaminate land and water. Burning mixed waste can release harmful smoke. Plastics can break into smaller pieces and remain in the environment for long periods. These effects are connected: a blocked drainage system, for example, can turn heavy rainfall into a serious neighbourhood problem."),
            ("A global development issue",
             "Waste management is a challenge in cities, towns and rural communities around the world. Rapid urbanisation, changing consumption patterns and limited collection infrastructure can place pressure on public services. Wealthier and poorer communities may experience very different levels of waste collection and environmental protection. This makes waste management both an environmental issue and a development issue."),
            ("From disposal to resource recovery",
             "A better system prevents unnecessary waste, separates reusable materials, supports safe recycling and ensures that remaining waste is handled responsibly. Materials such as suitable paper, metals, glass and some plastics may have recovery value when they are clean and properly sorted. Not every material can be recycled everywhere, so local collection arrangements matter.")
        ],
        "action": "Choose one common waste item and trace what should happen to it after use. Identify where the current system succeeds or fails."
    },

    {
        "title": "Understanding climate change",
        "pillar": PILLARS[0],
        "description": "Explore the science, causes and unequal effects of a changing global climate.",
        "minutes": 7,
        "content": [
            ("Weather and climate are different",
             "Weather describes short-term atmospheric conditions, such as today's temperature or rainfall. Climate describes patterns over much longer periods, usually decades. One cold day does not disprove global warming, just as one unusually hot day does not by itself prove climate change. Scientists study long-term observations to identify changes in temperature, rainfall, oceans and other parts of the climate system."),
            ("The greenhouse effect",
             "Certain gases in the atmosphere absorb and re-emit heat. This natural greenhouse effect keeps Earth warm enough to support life. Human activities have increased the concentration of greenhouse gases, particularly through burning coal, oil and gas, deforestation and some industrial and agricultural processes. This strengthens the greenhouse effect and contributes to global warming."),
            ("Impacts across the world",
             "Climate change can increase the intensity or likelihood of some extreme events, alter rainfall patterns, contribute to sea-level rise and place pressure on ecosystems. The effects differ by location. Small island states face serious sea-level risks, some regions experience severe heat, and farming communities may face changing growing seasons or unreliable rainfall."),
            ("Climate change and inequality",
             "Climate impacts are not experienced equally. Communities with limited savings, infrastructure, insurance or access to public services may find it harder to prepare and recover. People whose livelihoods depend on rain-fed agriculture, fishing or climate-sensitive natural resources can be particularly exposed. Climate action therefore involves questions of fairness, development finance and international cooperation."),
            ("Two important responses",
             "Mitigation means reducing greenhouse-gas emissions or increasing the removal of greenhouse gases from the atmosphere. Adaptation means adjusting systems and communities to actual or expected climate impacts. Renewable energy and energy efficiency can support mitigation. Early-warning systems, water conservation and climate-resilient infrastructure can support adaptation.")
        ],
        "action": "Identify one climate risk affecting a place you know and distinguish one possible adaptation response from one mitigation response."
    },

    {
        "title": "The importance of biodiversity",
        "pillar": PILLARS[0],
        "description": "Discover how living organisms and healthy ecosystems support life, economies and development.",
        "minutes": 6,
        "content": [
            ("What biodiversity means",
             "Biodiversity is the variety of life. It includes diversity within species, between species and among ecosystems. It covers plants, animals, fungi and microorganisms, as well as the habitats and ecological relationships that support them. Biodiversity is not limited to rare wildlife: crops, insects, soil organisms and ordinary plants are also part of it."),
            ("How ecosystems support people",
             "Healthy ecosystems provide services that societies depend on. Forests store carbon, protect soils and support water cycles. Pollinators contribute to food production. Wetlands can store water and reduce some flood impacts. Marine ecosystems support fisheries and livelihoods. These benefits are sometimes called ecosystem services because they support human wellbeing and economic activity."),
            ("Why biodiversity is under pressure",
             "Major pressures include habitat destruction, pollution, overexploitation of natural resources, invasive species and climate change. These pressures can interact. For example, habitat fragmentation may make it harder for species to move as temperatures and rainfall patterns change. When ecosystems lose species and ecological relationships, they may become less resilient."),
            ("A global and local perspective",
             "Biodiversity loss is a worldwide concern, but its effects are shaped by local ecosystems and livelihoods. Communities may depend on forests, grasslands, rivers, oceans or agricultural landscapes in different ways. Conservation works best when scientific knowledge is combined with the experiences and rights of people who live alongside these ecosystems."),
            ("Conservation and sustainable use",
             "Protecting biodiversity can involve restoring habitats, managing protected areas, reducing pollution, controlling invasive species and using natural resources responsibly. Conservation should also consider local communities, Indigenous knowledge, land rights and fair sharing of benefits. Long-term protection is more effective when people have meaningful reasons and opportunities to participate.")
        ],
        "action": "Choose one ecosystem and identify three ways people, plants or animals depend on it."
    },

    {
        "title": "The 3Rs of waste management",
        "pillar": PILLARS[0],
        "description": "Learn how reducing, reusing and recycling can prevent waste and conserve resources.",
        "minutes": 5,
        "content": [
            ("The waste hierarchy",
             "The 3Rs stand for Reduce, Reuse and Recycle. They are commonly presented in that order because preventing waste is generally preferable to dealing with it after it has been created. The wider waste hierarchy also includes repair, refurbishment, recovery and safe disposal. The best option depends on the material and the available systems."),
            ("Reduce: prevent waste before it exists",
             "Reducing means using fewer materials and avoiding unnecessary consumption. Examples include choosing durable products, avoiding excessive packaging, planning purchases and using digital documents when appropriate. Businesses can reduce waste by improving production processes and designing products that use fewer resources."),
            ("Reuse and repair: extend useful life",
             "Reuse means using an item again, either for its original purpose or a suitable new purpose. Repair restores an item so that it can continue serving its function. Reuse and repair can save money, preserve materials and create skills-based work. However, products must remain safe and suitable for their intended use."),
            ("Recycle: recover materials",
             "Recycling involves collecting and processing suitable materials so they can become inputs for new products. It usually requires sorting and clean material streams. Contamination can make recycling difficult or unsafe. Recycling also uses energy and resources, which is why reducing and reusing are important first steps."),
            ("Applying the 3Rs globally",
             "The 3Rs can be applied by households, schools, manufacturers, retailers and public institutions. Some countries have advanced collection systems, while others rely more heavily on informal collectors and community initiatives. Effective waste policy needs infrastructure, public education, product design and markets for recovered materials.")
        ],
        "action": "Select one item you use regularly. Write one realistic way to reduce its use, reuse it or recycle it responsibly."
    },

    {
        "title": "Protecting rivers and water sources",
        "pillar": PILLARS[0],
        "description": "Understand freshwater systems, pollution pathways and the shared responsibility to protect water.",
        "minutes": 6,
        "content": [
            ("Why freshwater matters",
             "Rivers, lakes, wetlands, groundwater and reservoirs support drinking-water supplies, agriculture, industry, energy production and ecosystems. Freshwater is limited and unevenly distributed. A community's access to safe water depends not only on rainfall but also on infrastructure, water quality, management and affordability."),
            ("How water becomes polluted",
             "Water pollution can come from untreated sewage, industrial discharge, agricultural chemicals, oil, plastics and poorly managed solid waste. Rain can carry pollutants from streets and fields into streams and rivers. Pollution may be visible, such as floating rubbish, or invisible, such as harmful microorganisms and dissolved chemicals."),
            ("Pollution moves through connected systems",
             "A river does not exist in isolation. It is part of a catchment or watershed: the area of land where water drains towards a common river, lake or outlet. Activities upstream can affect people and ecosystems downstream. This is why water protection often requires cooperation across communities, districts and even national borders."),
            ("Water governance and fairness",
             "Water management involves public institutions, communities, farmers, industries and households. Decisions about water allocation, pollution control and infrastructure can affect livelihoods and public health. Fair governance requires reliable information, clear responsibilities, public participation and attention to communities that have limited access to safe water."),
            ("Protecting water sources",
             "Useful measures include treating wastewater, maintaining sanitation systems, protecting riverbanks, reducing chemical runoff, preventing illegal dumping and monitoring water quality. Water conservation also matters, especially in areas facing drought or high demand. Reporting suspected pollution through appropriate channels can help responsible authorities investigate.")
        ],
        "action": "Identify a river, lake, wetland or groundwater source and list two activities that could threaten its quality."
    },

    {
        "title": "Why wetlands matter",
        "pillar": PILLARS[0],
        "description": "Explore wetlands as living ecosystems that support water regulation, biodiversity and livelihoods.",
        "minutes": 6,
        "content": [
            ("What is a wetland?",
             "Wetlands are areas where water covers the soil or remains close to the surface for enough time to shape the soil, plants and wildlife. They include marshes, swamps, peatlands, floodplains and some coastal ecosystems. Wetlands vary widely: some remain wet throughout the year, while others are seasonal."),
            ("Natural infrastructure",
             "Wetlands can store and slowly release water, trap some sediments and pollutants, support groundwater recharge in certain settings and reduce the effects of some floods. They also provide breeding and feeding habitats for many species. These functions make wetlands important natural infrastructure, although they cannot prevent every flood or remove every pollutant."),
            ("Livelihoods and economic value",
             "People may depend on wetlands for fishing, grazing, farming, tourism, materials and cultural activities. Their value is not only financial. Wetlands can support food security, local knowledge, biodiversity and community identity. Decisions about their use therefore involve ecological, economic and social considerations."),
            ("Threats and global significance",
             "Wetlands can be damaged by drainage, land conversion, pollution, unsustainable extraction, invasive species and changes in water flows. Wetland loss can reduce biodiversity and increase vulnerability to environmental hazards. International conservation efforts recognise that wetlands are important across freshwater, coastal and migratory wildlife systems."),
            ("Wise use and restoration",
             "Wetland protection involves understanding the ecosystem, respecting its natural water patterns, controlling pollution and managing nearby land use. Restoration may include removing barriers to water flow, re-establishing native vegetation and reducing damaging activities. Projects should be guided by ecological evidence and involve affected communities.")
        ],
        "action": "Find out whether a wetland exists in a place you know. Identify one benefit it provides and one pressure it may face."
    },

    {
        "title": "Indigenous trees and ecosystems",
        "pillar": PILLARS[0],
        "description": "Understand the ecological, cultural and economic value of native tree species around the world.",
        "minutes": 6,
        "content": [
            ("What makes a tree indigenous?",
             "An indigenous or native tree is one that occurs naturally in a particular region or ecosystem. Native species have developed ecological relationships with local soils, climate conditions, insects, birds and other organisms. A tree being native does not automatically mean it can grow well in every location; local conditions still matter."),
            ("Ecosystem functions",
             "Trees can provide shade, habitats, food, nesting sites and materials. Their roots can help stabilise soil, while leaves and branches contribute to nutrient cycles. Trees also store carbon as they grow. Different species provide different benefits, so healthy landscapes usually need a diversity of suitable plants rather than one species planted everywhere."),
            ("Culture and livelihoods",
             "Across the world, trees are connected to food, medicine, crafts, building materials, spiritual practices and community identity. Indigenous and local communities often hold detailed knowledge about native species and their uses. Such knowledge should be respected, and commercial use should not occur without appropriate consent and fair benefit-sharing."),
            ("Why planting the right tree matters",
             "Tree-planting projects sometimes focus on the number of seedlings planted rather than whether trees survive and support the ecosystem. Successful restoration considers native species, soil, rainfall, spacing, long-term maintenance and the needs of local wildlife. Planting unsuitable species can create ecological problems or require more water and care."),
            ("Global examples",
             "Different regions have distinct native trees: baobabs in parts of Africa, redwoods in parts of North America, eucalyptus species in Australia and many native forest species across Asia and South America. Their ecological roles differ, but the wider lesson is shared: restoration should be based on local biodiversity and sound ecological planning.")
        ],
        "action": "Research one native tree from a region you know. Find out what ecosystem role it plays and what conditions it needs to survive."
    },

    {
        "title": "Understanding air pollution",
        "pillar": PILLARS[0],
        "description": "Examine the sources, impacts and solutions associated with polluted air.",
        "minutes": 6,
        "content": [
            ("What is air pollution?",
             "Air pollution occurs when gases, particles or biological materials are present in the air at levels that can harm health or the environment. Some pollutants are released directly, while others form through chemical reactions in the atmosphere. Air quality can vary by place, season, weather and human activity."),
            ("Major sources",
             "Sources include vehicle exhaust, power generation, industrial processes, household fuels, agricultural burning, construction dust and open waste burning. Natural events such as wildfires and dust storms can also affect air quality. The relative importance of each source differs between cities, rural areas and countries."),
            ("Effects on people and ecosystems",
             "Air pollution is linked to respiratory and cardiovascular illness and can affect children, older people and those with existing health conditions. Some pollutants also damage crops, forests, buildings and ecosystems. Air pollution can cross administrative and national borders, meaning that one area's emissions may affect another."),
            ("Monitoring and evidence",
             "Air-quality monitoring measures pollutants such as fine particulate matter, nitrogen dioxide, ozone and sulphur dioxide. Monitoring stations, sensors and satellite observations can help identify patterns. Data must be interpreted carefully because low-cost sensors may have limitations and measurements depend on location and conditions."),
            ("Solutions at different levels",
             "Solutions include cleaner energy, efficient public transport, vehicle-emission controls, industrial pollution standards, clean household energy and better waste management. Individuals can make choices that reduce exposure, but lasting improvements require coordinated public policy, infrastructure and responsible business practices.")
        ],
        "action": "Identify a possible source of air pollution in a place you know and suggest one action that could reduce emissions."
    },

    {
        "title": "Electronic waste and responsible disposal",
        "pillar": PILLARS[0],
        "description": "Explore the environmental and economic challenges created by discarded electronic products.",
        "minutes": 6,
        "content": [
            ("What counts as electronic waste?",
             "Electronic waste, often called e-waste, includes discarded electrical and electronic equipment such as phones, computers, televisions, chargers, household appliances and some batteries. It is a growing global concern as technology use expands and products are replaced more frequently."),
            ("A mixture of hazards and valuable materials",
             "Electronic products can contain materials that require careful handling, including certain metals, chemicals and battery components. They may also contain recoverable materials such as copper, aluminium, iron and selected precious metals. Safe recovery requires appropriate equipment, trained workers and controlled processes."),
            ("Why informal handling can be dangerous",
             "Unsafe dismantling, open burning and crude chemical extraction can expose people and the environment to harmful substances. Workers may face risks when equipment is broken apart without protective measures. E-waste should not be burned or dismantled casually, and damaged batteries require particular care."),
            ("The global e-waste challenge",
             "Electronic products are designed, manufactured, sold, used and discarded across international supply chains. Waste may cross borders, and recycling capacity differs widely between countries. Responsible systems require producer responsibility, repair options, collection points, safe recycling facilities and enforcement against illegal dumping or unsafe processing."),
            ("Moving towards responsible electronics",
             "Consumers can extend product life through appropriate care and repair, use authorised take-back or collection programmes where available, and protect personal information before devices are handed over. Manufacturers and governments can support durable design, repairability, safe collection and transparent recycling systems.")
        ],
        "action": "Find out how unwanted phones, batteries or computers can be handed over safely in your area. Do not dismantle or burn electronic equipment."
    },

    {
        "title": "Soil conservation",
        "pillar": PILLARS[0],
        "description": "Learn how soil supports food systems, ecosystems and climate resilience.",
        "minutes": 6,
        "content": [
            ("Soil is a living resource",
             "Soil is more than dirt. It contains minerals, organic matter, water, air and living organisms. Soil organisms help break down organic material and recycle nutrients. Healthy soil supports plant growth, stores water and provides a foundation for agriculture, forests and many ecosystems."),
            ("Understanding soil degradation",
             "Soil degradation occurs when soil loses quality or its ability to perform important functions. Causes include erosion by wind and water, nutrient depletion, compaction, salinisation, pollution and loss of organic matter. Poor land management can accelerate these processes, while extreme rainfall and drought can increase pressure."),
            ("Why erosion matters",
             "When topsoil is removed, land may lose nutrients and water-holding capacity. Sediment can enter rivers and reservoirs, affecting water quality and infrastructure. Soil erosion can therefore affect food production, household incomes, ecosystems and public services beyond the farm or site where it begins."),
            ("Conservation approaches",
             "Practices may include maintaining vegetation cover, planting cover crops, using contour farming where appropriate, reducing unnecessary soil disturbance, managing grazing and restoring degraded land. No single method works everywhere. Conservation should reflect local soils, slope, rainfall, farming systems and available resources."),
            ("Soil, climate and food security",
             "Soils store large amounts of carbon and influence how water moves through landscapes. Sustainable soil management can support agricultural resilience and reduce some forms of land degradation. However, soil restoration takes time, and claims about carbon benefits should be based on reliable measurements.")
        ],
        "action": "Identify one activity that could cause soil erosion in a landscape you know and one practical conservation measure."
    },

    {
        "title": "Climate adaptation",
        "pillar": PILLARS[0],
        "description": "Understand how households, cities, businesses and countries prepare for climate impacts.",
        "minutes": 7,
        "content": [
            ("What adaptation means",
             "Climate adaptation is the process of adjusting human or natural systems to actual or expected climate conditions and their effects. It aims to reduce harm or make use of possible opportunities. Adaptation does not mean that climate change is harmless; it recognises that some impacts are already occurring and further changes are expected."),
            ("Adaptation depends on local risk",
             "A coastal city may need to plan for sea-level rise and storm surges. A dryland farming area may focus on water storage, soil health and drought-resilient crops. A densely populated city may need heat-health plans, drainage maintenance and early-warning systems. Good adaptation begins by understanding hazards, exposure and vulnerability."),
            ("Household and community responses",
             "Communities can improve preparedness through reliable information, safe water storage, emergency plans, community support networks and climate-aware land use. Farmers may adjust planting dates, diversify crops or use water-efficient practices where suitable. These actions should be based on evidence and should not place unreasonable costs on households with limited resources."),
            ("Infrastructure and public planning",
             "Roads, bridges, drainage, schools, hospitals and energy systems need to be designed and maintained with future climate risks in mind. Public planning can reduce exposure by avoiding unsafe development areas and protecting natural buffers. Adaptation is more effective when it is included in ordinary development decisions rather than treated as a separate activity."),
            ("Avoiding maladaptation",
             "Maladaptation occurs when an action intended to reduce climate risk creates new risks or increases vulnerability elsewhere. For example, a poorly planned flood barrier may transfer floodwater to another community. Adaptation should therefore consider long-term impacts, environmental effects, fairness and the voices of affected people.")
        ],
        "action": "Choose one climate-related risk and outline a response at household level and another at community or government level."
    },

    {
        "title": "The circular economy",
        "pillar": PILLARS[0],
        "description": "Explore how products and materials can remain useful instead of following a take-make-dispose pattern.",
        "minutes": 7,
        "content": [
            ("From linear to circular systems",
             "A traditional linear economy often follows a take-make-use-dispose pattern: resources are extracted, turned into products, used and discarded. A circular economy aims to reduce waste and keep products, components and materials in use for as long as practical. It also seeks to reduce pollution and regenerate natural systems."),
            ("Designing waste out",
             "Circular thinking begins before a product is made. Designers can consider durability, repair, reuse, safe materials and the ability to recover components. Businesses can reduce packaging, offer repair services and develop take-back systems. These decisions influence how much waste is created later."),
            ("Business models in a circular economy",
             "Examples include repair services, second-hand markets, product leasing, refurbishment, remanufacturing and material recycling. Some businesses earn income by maintaining products rather than selling replacements. These models can create jobs and reduce demand for new raw materials, although their success depends on cost, quality and customer demand."),
            ("Global supply chains and responsibility",
             "Products often use materials sourced from several countries and are sold in international markets. Circular systems therefore require cooperation between designers, manufacturers, consumers, repairers, recyclers and governments. Product standards, information about materials and responsible supply chains can support this transition."),
            ("Circular does not mean impact-free",
             "Recycling and reuse still require transport, energy, labour and infrastructure. Some materials lose quality during recycling, and some products are difficult to recover safely. A circular economy is not simply about recycling more; it is about reducing unnecessary material use and designing systems that prevent waste in the first place.")
        ],
        "action": "Choose a product you use. Suggest one way its design, repair, sharing or collection system could become more circular."
    },

    {
        "title": "Community clean-up campaigns",
        "pillar": PILLARS[0],
        "description": "Learn how organised community action can improve public spaces and support long-term waste solutions.",
        "minutes": 5,
        "content": [
            ("What a clean-up campaign can achieve",
             "A community clean-up brings people together to remove litter or improve a shared space. It can make public areas safer and more pleasant, raise awareness and encourage cooperation. It can also help residents identify waste-management problems that need attention beyond a single event."),
            ("Planning before action",
             "A useful campaign begins by identifying the site, the type of waste, the people responsible for the area and the available collection arrangements. Organisers should consider permission, safe access, suitable equipment, drinking water, supervision and how collected waste will be transported and disposed of."),
            ("Safety and inclusion",
             "Participants should not handle unknown chemicals, sharp objects, medical waste, damaged batteries or other hazardous materials. Such materials need appropriate reporting and trained handling. Campaigns should also be accessible and inclusive, with tasks suited to participants' abilities and appropriate adult supervision where young people are involved."),
            ("From one event to lasting change",
             "A clean-up alone does not solve the causes of littering or illegal dumping. Long-term improvement may require reliable waste collection, accessible bins, public education, enforcement, producer responsibility and convenient recycling options. Campaigns are strongest when they connect residents with responsible institutions and service providers."),
            ("Measuring impact",
             "Organisers can record the area covered, types of waste collected, number of participants and issues identified. These records help assess progress and plan future activities. Data should be collected consistently and should not exaggerate the amount of waste removed or the environmental impact achieved.")
        ],
        "action": "Design a simple clean-up plan that identifies the location, permissions, safe tasks, collection arrangements and how success will be measured."
    },

    # --------------------------------------------------------
    # GOVERNANCE & CIVIC EDUCATION — 14 TO 25
    # --------------------------------------------------------

    {
        "title": "Who is responsible for a clean community?",
        "pillar": PILLARS[1],
        "description": "Explore how residents, businesses, institutions and public authorities share responsibility for public spaces.",
        "minutes": 6,
        "content": [
            ("Shared responsibility does not mean identical roles",
             "A clean and healthy community depends on different actors carrying out different responsibilities. Households can manage their waste responsibly, businesses can reduce and handle commercial waste, service providers can collect and transport it, and public institutions can plan, regulate and monitor services."),
            ("The role of public institutions",
             "Local and national authorities may be responsible for public sanitation, waste-service planning, environmental regulation and public education. Their exact duties differ by country and legal system. Clear standards, adequate resources and transparent reporting help residents understand what services should be provided."),
            ("The role of businesses",
             "Businesses influence waste through product design, packaging, purchasing, production and disposal. Responsible businesses can reduce material use, separate waste, support take-back programmes and work with legitimate recyclers. Producers can also help fund systems for collecting and recovering products after use."),
            ("The role of communities",
             "Residents and community organisations can identify service gaps, participate in planning, report problems through appropriate channels and support public education. Community action should complement public services rather than become an excuse for institutions to avoid their responsibilities."),
            ("Cooperation and accountability",
             "Effective environmental management requires coordination. If waste is not collected, the problem may involve infrastructure, funding, service delivery, public behaviour or unclear responsibilities. Understanding the system helps communities ask constructive questions and identify realistic solutions.")
        ],
        "action": "Choose one environmental problem and identify the responsibilities of residents, businesses and public institutions in addressing it."
    },

    {
        "title": "Understanding civic responsibility",
        "pillar": PILLARS[1],
        "description": "Learn how people contribute to society through rights, duties, participation and respect for others.",
        "minutes": 6,
        "content": [
            ("What civic responsibility means",
             "Civic responsibility refers to the ways people contribute to the wellbeing of the communities and political systems in which they live. It can include respecting the rights of others, following fair laws, staying informed, participating in public discussions and helping protect shared resources."),
            ("Rights and responsibilities work together",
             "People have rights, including rights related to expression, participation and access to public information, subject to the applicable legal framework. Responsible civic life also involves recognising that other people hold rights too. Participation should respect dignity, equality and peaceful disagreement."),
            ("Participation beyond elections",
             "Civic participation is not limited to voting. Depending on age and national laws, people may take part in public consultations, school councils, community meetings, volunteering, advocacy, research and civic education. Young people can contribute ideas and evidence even when they are not yet eligible to vote."),
            ("Informed and responsible engagement",
             "Constructive participation requires checking information, listening to different perspectives and distinguishing evidence from rumour. People should be able to question decisions without harassment or intimidation. Peaceful and informed engagement can help institutions understand community needs."),
            ("Civic responsibility in a connected world",
             "Digital platforms allow people to discuss public issues across borders, but they also create risks such as misinformation, harassment and privacy violations. Responsible digital citizenship includes verifying claims, respecting others and thinking carefully before sharing content.")
        ],
        "action": "Identify one community issue and describe a peaceful, informed way people your age could contribute to addressing it."
    },

    {
        "title": "What is environmental governance?",
        "pillar": PILLARS[1],
        "description": "Understand the institutions, rules and decision-making processes that shape environmental protection.",
        "minutes": 7,
        "content": [
            ("Defining environmental governance",
             "Environmental governance refers to the institutions, laws, policies, organisations and processes through which societies make decisions about the environment and natural resources. It includes who has authority, who participates, how decisions are implemented and how responsible actors are held accountable."),
            ("More than government alone",
             "Government is important, but environmental governance also involves communities, businesses, civil society organisations, researchers, international institutions and Indigenous peoples. These actors may have different interests and levels of influence. Good governance creates fair ways for them to contribute and resolve disagreements."),
            ("Rules and institutions",
             "Environmental governance may involve laws on pollution, land use, protected areas, water management, biodiversity and climate action. Institutions are responsible for implementing and monitoring these rules. Effective systems need clear mandates, adequate resources, reliable evidence and fair enforcement."),
            ("Global environmental cooperation",
             "Many environmental challenges cross national borders. Climate change, ocean pollution, biodiversity loss and shared river systems require cooperation between countries. International agreements can establish common goals and reporting expectations, but implementation often depends on national policies, finance and institutional capacity."),
            ("What makes governance effective?",
             "Important principles include transparency, participation, accountability, fairness, access to information and respect for the rule of law. Governance also needs to recognise power imbalances. Communities most affected by environmental decisions should have meaningful opportunities to influence them.")
        ],
        "action": "Choose an environmental issue and identify the institutions and community groups that should be involved in making decisions about it."
    },

    {
        "title": "Community participation in decision-making",
        "pillar": PILLARS[1],
        "description": "Explore why people affected by development decisions should have a meaningful voice in shaping them.",
        "minutes": 6,
        "content": [
            ("What meaningful participation involves",
             "Community participation means more than informing people after a decision has already been made. It involves giving affected people accessible information and genuine opportunities to influence decisions. Participation can happen through meetings, surveys, public hearings, community committees and other suitable methods."),
            ("Why local knowledge matters",
             "Residents often understand everyday conditions that may not appear in official reports. They may know where flooding occurs, which services are unreliable or how a proposed project could affect livelihoods. Combining local experience with technical evidence can improve planning and reveal risks early."),
            ("Participation and power",
             "Not everyone has the same time, confidence, resources or access to decision-makers. Women, young people, people with disabilities, remote communities and disadvantaged groups may face barriers. Inclusive processes need accessible venues, suitable languages, clear information and deliberate efforts to hear less powerful voices."),
            ("From consultation to influence",
             "A consultation is meaningful when organisers explain the issue, invite contributions, record concerns and show how feedback influenced the final decision. If suggestions cannot be adopted, decision-makers should explain why. Participation without feedback can weaken trust."),
            ("Participation in development projects",
             "Community participation can improve the design, implementation and monitoring of projects. It can help identify unintended consequences, build local ownership and strengthen accountability. It does not guarantee agreement, but it can make disagreement more informed and manageable.")
        ],
        "action": "Think of a public project in a place you know. Identify who should be consulted and how their views could influence the final decision."
    },

    {
        "title": "Transparency and accountability",
        "pillar": PILLARS[1],
        "description": "Understand how open information and answerable decision-making strengthen public trust.",
        "minutes": 6,
        "content": [
            ("Understanding transparency",
             "Transparency means that relevant information about decisions, rules, activities and the use of resources is accessible and understandable. It allows people to see how decisions are made and what institutions are doing. Information is not truly accessible if it is hidden in technical language or unavailable to the people who need it."),
            ("Understanding accountability",
             "Accountability means that people and institutions with responsibilities can be asked to explain their actions and can face appropriate consequences when they fail to meet their duties. Accountability may involve internal procedures, public oversight, audits, courts, regulators or other lawful mechanisms."),
            ("Why the two principles are connected",
             "Transparency helps people identify what has happened, while accountability provides ways to question and respond to it. Publishing a budget, for example, is a transparency measure. Explaining spending decisions and investigating misuse are accountability measures."),
            ("Application to environmental services",
             "In waste management, transparency may include publishing collection schedules, service standards, budgets and performance information. Accountability may involve responding to complaints, investigating service failures and explaining how funds and equipment are used."),
            ("Building trust responsibly",
             "Open information can strengthen trust, but information must be accurate, timely and presented responsibly. Personal information should be protected, and allegations should not be treated as facts without evidence. Effective accountability uses fair procedures rather than public accusation or harassment.")
        ],
        "action": "Write two respectful questions residents could ask about the delivery or funding of a public environmental service."
    },

    {
        "title": "The role of local authorities",
        "pillar": PILLARS[1],
        "description": "Explore how local government and municipal institutions shape everyday services and sustainable settlements.",
        "minutes": 7,
        "content": [
            ("What local authorities do",
             "Local authorities are public institutions responsible for aspects of local administration and service delivery. Their powers vary between countries. Depending on the legal framework, they may be involved in land-use planning, roads, sanitation, waste collection, public spaces, local infrastructure and community services."),
            ("Why local government matters",
             "Many development issues are experienced locally. Residents interact with roads, drainage, markets, public spaces, water and sanitation systems in their everyday lives. Local institutions are often closer to these service needs and can help translate national policies into local action."),
            ("Planning and limited resources",
             "Local authorities must make decisions about priorities, budgets, infrastructure and maintenance. Population growth, informal settlement patterns, limited revenue and ageing infrastructure can place pressure on services. Good planning requires reliable information and fair ways of deciding how resources should be allocated."),
            ("Working with communities and other actors",
             "Local authorities do not operate alone. They may work with national government, private service providers, community organisations, schools and residents. Clear contracts, public information and monitoring are important when services are delivered through partnerships."),
            ("Comparing local systems globally",
             "Municipal systems differ widely around the world. Some cities have extensive public transport and waste infrastructure, while others face gaps in basic services. Comparing systems can reveal useful ideas, but solutions must be adapted to local laws, budgets, geography and community needs.")
        ],
        "action": "Choose one local public service and identify what the responsible authority does, what residents need and how service performance could be improved."
    },

    {
        "title": "Environmental rights and responsibilities",
        "pillar": PILLARS[1],
        "description": "Explore the relationship between a healthy environment, human wellbeing and responsible conduct.",
        "minutes": 6,
        "content": [
            ("The environment and human wellbeing",
             "People depend on clean air, safe water, healthy food, stable ecosystems and safe places to live. Environmental harm can affect health, housing, livelihoods, culture and development opportunities. This is why environmental protection is closely connected to human rights and social justice."),
            ("Environmental rights in different legal systems",
             "Countries recognise environmental rights in different ways. Some constitutions explicitly recognise a right to a clean, healthy or satisfactory environment. Other protections may appear in laws, court decisions or international human-rights frameworks. The exact legal rights and remedies depend on the relevant jurisdiction."),
            ("Access to information and participation",
             "People need information about environmental risks that may affect them. Participation allows communities to contribute to decisions about projects, land use and natural resources. Access to justice provides ways to challenge harmful decisions or seek remedies where legal rights have been violated."),
            ("Responsibilities and shared protection",
             "Environmental rights do not remove responsibilities. Individuals, businesses and institutions all influence environmental quality. Responsible conduct includes avoiding pollution, respecting environmental rules, using resources carefully and ensuring that activities do not unfairly harm other people."),
            ("A global justice perspective",
             "Environmental burdens are not distributed equally. Communities with fewer resources may live closer to pollution sources or have less ability to recover from environmental damage. Environmental justice asks whether protection, decision-making power and environmental benefits are shared fairly.")
        ],
        "action": "Identify one environmental condition that affects people's wellbeing and explain which rights, responsibilities or public duties may be relevant."
    },

    {
        "title": "Youth participation in governance",
        "pillar": PILLARS[1],
        "description": "Discover how young people can contribute to public decisions and community development.",
        "minutes": 6,
        "content": [
            ("Why youth participation matters",
             "Young people are affected by decisions about education, employment, technology, climate, public services and the future of their communities. Their experiences and ideas can improve policy and development programmes. Youth participation also helps build civic knowledge and confidence."),
            ("Participation takes different forms",
             "Young people can contribute through school councils, youth organisations, community projects, public consultations, research, advocacy and constructive dialogue. Digital platforms can widen participation, but online engagement should complement rather than replace opportunities for people who have limited internet access."),
            ("Tokenism versus meaningful influence",
             "Tokenism occurs when young people are invited to an activity mainly for appearance, without real influence over decisions. Meaningful participation gives them relevant information, space to express views, respect and feedback about how their contributions were used."),
            ("Barriers to participation",
             "Barriers can include age restrictions, limited information, transport costs, inaccessible meetings, discrimination and the belief that young people have nothing useful to contribute. Institutions can reduce these barriers by creating safe, inclusive and age-appropriate participation opportunities."),
            ("Youth leadership and responsibility",
             "Youth leadership involves listening, learning, working with others and taking responsibility for decisions. Effective youth participation should be peaceful, evidence-informed and respectful of different views. It should also avoid placing responsibilities on young people that properly belong to public institutions.")
        ],
        "action": "Choose one issue affecting young people and outline a respectful way to present evidence and recommendations to decision-makers."
    },

    {
        "title": "Public consultations",
        "pillar": PILLARS[1],
        "description": "Learn how public consultations gather community views before policies and projects are decided.",
        "minutes": 6,
        "content": [
            ("What a public consultation is",
             "A public consultation is a process through which institutions invite people to share views about a proposed policy, project, law or decision. It can help decision-makers understand public needs, identify risks and consider alternatives before taking action."),
            ("The stages of a useful consultation",
             "A consultation should explain what is being proposed, why the decision is needed, what alternatives exist and how people can respond. Organisers then collect and analyse contributions, consider the evidence and communicate the outcome. The exact process depends on the issue and legal requirements."),
            ("Making participation accessible",
             "People cannot contribute effectively if information is unclear or opportunities are inaccessible. Useful approaches may include plain-language summaries, translation, accessible venues, online and offline options, suitable meeting times and targeted engagement with affected groups."),
            ("Consultation is not automatic agreement",
             "A consultation does not mean that every suggestion must be accepted or that everyone will agree. Decision-makers should consider contributions fairly and explain the reasons for their choices. A process that ignores feedback or has already made the decision may be consultation in name only."),
            ("Global examples",
             "Public consultations are used in areas such as transport planning, environmental impact assessment, land-use decisions and public budgeting. Their quality varies. Strong processes make information available early, include affected groups and show how public contributions influenced the outcome.")
        ],
        "action": "Choose a proposed community project and list three questions residents should be able to ask before it is approved."
    },

    {
        "title": "Environmental justice",
        "pillar": PILLARS[1],
        "description": "Examine how environmental risks, benefits and decision-making power are distributed across society.",
        "minutes": 7,
        "content": [
            ("What environmental justice means",
             "Environmental justice focuses on fairness in the way environmental harms and benefits are distributed, how decisions are made and whether people are recognised and respected. It asks who experiences pollution, who benefits from natural resources and whose voices influence environmental policy."),
            ("Unequal exposure to environmental harm",
             "Low-income communities and marginalised groups may face greater exposure to pollution, unsafe housing, poor sanitation or climate risks. This can happen because of historical inequalities, land-use decisions, limited political influence and unequal access to services. The pattern differs between countries and communities."),
            ("Three useful dimensions",
             "Distributive justice concerns how environmental burdens and benefits are shared. Procedural justice concerns whether decision-making processes are fair and inclusive. Recognition justice concerns whether different identities, experiences, cultures and knowledge systems are respected."),
            ("Environmental justice across borders",
             "Global supply chains can shift environmental costs from consumers and manufacturers to communities where extraction, production or waste processing occurs. Climate change also raises questions about historical emissions, responsibility, finance and the capacity of countries to adapt."),
            ("Building fairer environmental decisions",
             "Fair approaches require accessible information, meaningful participation, protection from discrimination, effective enforcement and attention to communities facing the greatest risks. Environmental justice does not mean every community has identical needs; it means decisions should respond fairly to different circumstances.")
        ],
        "action": "Identify an environmental problem and ask: who is most affected, who makes the decisions and who receives the benefits?"
    },

    {
        "title": "Community reporting and responsible citizenship",
        "pillar": PILLARS[1],
        "description": "Learn how to report public concerns accurately, safely and through appropriate channels.",
        "minutes": 5,
        "content": [
            ("Why community reporting matters",
             "Residents often notice problems before they appear in formal reports. These may include illegal dumping, damaged infrastructure, blocked drains, pollution or unsafe public spaces. Responsible reporting can help institutions identify issues and decide whether investigation or action is needed."),
            ("What makes a useful report?",
             "A useful report describes what was observed, where it happened, when it happened and why it may be a concern. It separates direct observations from assumptions. Where appropriate and safe, photographs or other evidence may help, but evidence should be collected lawfully and without putting anyone at risk."),
            ("Choosing the right channel",
             "Reporting channels differ by country and issue. They may include local authorities, environmental regulators, service providers, school management or established community reporting systems. People should use verified contact details and follow the relevant process rather than relying on rumours or unofficial claims."),
            ("Privacy and responsible communication",
             "Reports should avoid exposing private information, making unsupported accusations or sharing images that identify people unnecessarily. A report should focus on the issue and relevant evidence. Publicly posting allegations can create harm and may interfere with a proper investigation."),
            ("Closing the feedback loop",
             "Where possible, reporting systems should acknowledge complaints, provide reference numbers and explain what action will follow. Institutions can improve trust by communicating progress and reasons when action cannot be taken immediately.")
        ],
        "action": "Draft a short, factual report about a hypothetical community environmental problem without naming or accusing an individual."
    },

    {
        "title": "Peaceful dialogue and community problem-solving",
        "pillar": PILLARS[1],
        "description": "Explore how listening, negotiation and fair processes help communities address disagreement.",
        "minutes": 6,
        "content": [
            ("Why communities disagree",
             "People may share a common goal but disagree about how to achieve it. For example, a development project may create jobs while also raising concerns about land, noise, pollution or access to resources. Different experiences and priorities can lead to genuine disagreement."),
            ("Dialogue as a practical tool",
             "Peaceful dialogue creates space for people to explain concerns, ask questions and understand other perspectives. It does not require everyone to agree. Good dialogue involves listening, speaking respectfully, checking facts and identifying the issues that can be addressed."),
            ("Negotiation and shared solutions",
             "Negotiation involves people discussing options to reach an agreement or manage differences. Useful approaches identify shared interests, consider alternatives and clarify responsibilities. Agreements should be realistic, fair and clear about what happens next."),
            ("Inclusion and power differences",
             "A meeting is not automatically fair simply because everyone is invited. Some participants may have more influence, confidence or access to information than others. Facilitators can support fairness by setting clear rules, allowing different forms of contribution and preventing intimidation."),
            ("From disagreement to cooperation",
             "Community problem-solving works best when decisions are documented, responsibilities are agreed and progress is reviewed. Where serious legal or safety issues arise, dialogue may need to be supported by appropriate professional or institutional processes.")
        ],
        "action": "Imagine two groups disagree about the location of a community recycling point. Suggest a fair process for hearing concerns and comparing possible locations."
    },

]
    # --------------------------------------------------------
    # BUSINESS & ENTREPRENEURSHIP — 26 TO 37
    # --------------------------------------------------------

    {
        "title": "Can waste become wealth?",
        "pillar": PILLARS[2],
        "description": "Explore how recovered materials can create economic value, livelihoods and environmental benefits.",
        "minutes": 7,
        "content": [
            ("Waste as a resource",
             "Some materials that people discard can still have economic value. Metals, paper, glass, selected plastics, textiles and electronic components may be collected, sorted, repaired or processed for further use. Whether a material has value depends on its condition, quality, quantity, transport costs and the existence of buyers or processing facilities."),
            ("The value chain",
             "A recycling value chain can involve collection, aggregation, sorting, cleaning, processing, manufacturing and sale. Different participants may earn income at different stages. For example, collectors may supply sorted materials to a larger buyer, while processors turn recovered materials into inputs for new products."),
            ("Economic opportunities and decent work",
             "Waste recovery can support livelihoods and entrepreneurship, but work must be safe and fairly organised. Workers may face risks from sharp materials, hazardous substances, traffic and unstable prices. Better equipment, training, protective measures and fair payment can improve working conditions."),
            ("Why markets matter",
             "Collecting materials does not automatically create a profitable business. Entrepreneurs need to know whether buyers exist, what quality they require, how much they pay and what transport or storage costs will be involved. If there is no reliable market, recovered materials may accumulate rather than being recycled."),
            ("A global circular-economy opportunity",
             "Countries are exploring ways to reduce waste and recover resources through recycling, repair, reuse and product redesign. Opportunities differ across regions because infrastructure, regulation, technology and consumer demand vary. Successful ventures respond to real market conditions rather than assuming every waste material is valuable.")
        ],
        "action": "Choose one recoverable material and map a possible journey from collection to a buyer or manufacturer. Identify two costs and one possible source of income."
    },

    {
        "title": "Introduction to entrepreneurship",
        "pillar": PILLARS[2],
        "description": "Understand how entrepreneurs identify needs, develop solutions and organise resources to create value.",
        "minutes": 6,
        "content": [
            ("What entrepreneurship involves",
             "Entrepreneurship is the process of identifying an opportunity or problem and organising resources to create a product, service or venture. Entrepreneurs may operate for profit, social benefit or a combination of both. They take informed risks, test ideas and adapt when evidence shows that something is not working."),
            ("Start with a real problem",
             "A business idea should respond to a need rather than simply reflect what its founder wants to sell. Problems can include unreliable services, high costs, limited access to products or environmental challenges. Observing people and asking questions helps entrepreneurs understand whether a problem is important enough for a solution."),
            ("Testing an idea",
             "Entrepreneurs can test an idea through interviews, small prototypes, demonstrations or trial services. Testing helps reveal whether people understand the offer, whether they would use it and what improvements are needed. A small test can reduce the risk of spending too much money on an unproven idea."),
            ("Resources and business skills",
             "A venture may require time, knowledge, equipment, materials, finance, partners and legal permissions. Entrepreneurs also need communication, planning, customer service and record-keeping skills. Not every resource must be owned; some can be shared, rented or accessed through partnerships."),
            ("Learning from failure",
             "A project may not attract enough customers or may cost more than expected. This does not automatically mean the founder should give up. Reviewing evidence, identifying the cause and adjusting the model can help. Responsible entrepreneurship also means recognising when an idea is unsafe, unfair or environmentally harmful.")
        ],
        "action": "Identify a problem affecting a group of people. Describe who experiences it, what solution could help and how you would test the idea before investing heavily."
    },

    {
        "title": "What is a green business?",
        "pillar": PILLARS[2],
        "description": "Explore enterprises that reduce environmental harm while creating useful products, services and livelihoods.",
        "minutes": 6,
        "content": [
            ("Defining a green business",
             "A green business provides products or services, or operates in ways that aim to reduce environmental harm and support more sustainable resource use. Examples may include renewable-energy services, repair businesses, recycling, sustainable transport, water-efficiency services and responsible agriculture."),
            ("Environmental claims need evidence",
             "A business should not describe itself as sustainable simply because it uses green colours or promotes one environmentally friendly activity. Its wider impacts matter, including energy use, materials, transport, labour conditions and waste. Unsupported claims can become greenwashing: presenting an activity or product as more environmentally responsible than the evidence supports."),
            ("Balancing environmental and economic goals",
             "A green business still needs customers, reliable operations, realistic costs and a workable income model. Environmental benefits must be considered alongside financial sustainability and social effects. A business that cannot continue operating may struggle to deliver long-term benefits."),
            ("Examples across the world",
             "Green enterprises operate in many sectors. They may install solar systems, provide energy audits, repair electronics, collect recyclable materials, produce lower-impact packaging or support sustainable farming. The most suitable opportunity depends on local needs, technology, regulations and available markets."),
            ("Measuring real impact",
             "Businesses can track indicators such as materials recovered, energy saved, water used, emissions reduced or products repaired. Measurement should use clear methods and honest reporting. It is important to avoid claiming that an activity has prevented a specific amount of pollution unless there is reliable evidence.")
        ],
        "action": "Describe a green business idea and identify the customer, the environmental benefit and one measure that could show whether the benefit is real."
    },

    {
        "title": "Understanding customers",
        "pillar": PILLARS[2],
        "description": "Learn how customer needs, behaviour and feedback influence products and services.",
        "minutes": 5,
        "content": [
            ("Who is a customer?",
             "A customer is a person or organisation that buys or uses a product or service. The person who pays may not always be the person who uses it. For example, a school may purchase a service that benefits learners, teachers and the wider community."),
            ("Understanding needs rather than guessing",
             "Customers may care about price, quality, convenience, reliability, safety, accessibility and trust. Entrepreneurs should investigate these priorities instead of assuming that everyone wants the same thing. Different groups can experience the same problem in different ways."),
            ("Customer research",
             "Useful methods include interviews, surveys, observation and small product trials. Questions should be clear and neutral. Entrepreneurs should avoid pressuring people to give positive feedback and should protect personal information collected during research."),
            ("Customer experience",
             "A good product can still fail if it is difficult to access, unreliable or poorly supported. Customer experience includes how people discover an offer, make a purchase, receive the service, ask for help and resolve problems."),
            ("Using feedback responsibly",
             "Feedback can reveal what customers value and where improvements are needed. Not every suggestion can be adopted, and a few opinions may not represent an entire market. Entrepreneurs should look for patterns and compare feedback with actual behaviour and other evidence.")
        ],
        "action": "Choose a product or service idea and write three neutral questions you would ask potential customers before launching it."
    },

    {
        "title": "Market research for beginners",
        "pillar": PILLARS[2],
        "description": "Discover how to investigate demand, competitors, prices and market conditions before launching a venture.",
        "minutes": 6,
        "content": [
            ("What market research does",
             "Market research gathers information about customers, competitors and the conditions in which a business may operate. It helps entrepreneurs understand whether a problem exists, whether people want a solution and what alternatives are already available."),
            ("Primary and secondary research",
             "Primary research is information collected directly for a particular question, such as interviews, surveys or observations. Secondary research uses information that already exists, such as published reports, official statistics, academic studies and industry publications. Both can be useful, but their quality and relevance must be checked."),
            ("Understanding competitors",
             "Competitors may offer similar products or different ways of solving the same problem. Researching them can reveal prices, service quality, customer expectations and gaps in the market. Competition is not always direct: a customer may choose to do nothing or use an informal alternative."),
            ("Demand, price and affordability",
             "People may say they like an idea but still be unable or unwilling to pay for it. Research should explore how often customers need the service, what they currently spend and what price is realistic. Affordability and willingness to pay are related but not identical."),
            ("Making decisions from evidence",
             "Research does not guarantee success. It reduces uncertainty and helps entrepreneurs make better-informed decisions. Findings should be recorded honestly, including evidence that challenges the original idea. Small tests can help determine whether further investment is justified.")
        ],
        "action": "For a proposed environmental service, identify one customer group, two competitors or alternatives and three questions your research must answer."
    },

    {
        "title": "Understanding revenue and profit",
        "pillar": PILLARS[2],
        "description": "Learn the difference between income, costs and profit when assessing business performance.",
        "minutes": 6,
        "content": [
            ("Revenue is not profit",
             "Revenue is the money a business earns from selling goods or services before expenses are deducted. Profit is what remains after relevant costs are subtracted from revenue. A business can have high sales but still make a loss if its costs are too high."),
            ("Understanding costs",
             "Costs may include materials, transport, wages, rent, electricity, packaging, equipment maintenance and communication. Some costs change with the number of products or services delivered, while others remain relatively stable over a period. Entrepreneurs should identify both when planning."),
            ("A simple example",
             "Imagine a small repair service earns 200 units of currency from a job. If the materials, transport and other costs for that job total 130 units, the amount remaining before any other uncounted expenses is 70 units. The example shows why revenue alone does not reveal whether a business is performing well."),
            ("Cash flow matters too",
             "Cash flow tracks money entering and leaving a business over time. A business may record sales but still struggle to pay bills if customers pay late. Planning payment dates, keeping records and maintaining an appropriate cash reserve can help manage this risk."),
            ("Using financial information",
             "Simple records of sales, expenses, stock and payments help entrepreneurs understand performance. Financial information should be accurate and updated regularly. Profit should not be confused with cash available, and personal money should be distinguished from business money where possible.")
        ],
        "action": "List three possible costs for a recycling or repair business. Explain why the money received from customers is not automatically the business's profit."
    },

    {
        "title": "Building a simple business model",
        "pillar": PILLARS[2],
        "description": "Explore how a venture creates value, reaches customers and supports its operations financially.",
        "minutes": 7,
        "content": [
            ("What a business model explains",
             "A business model describes how a venture creates, delivers and captures value. It explains what the business offers, who it serves, how it reaches customers, what resources it needs and how it earns income or sustains its activities."),
            ("The problem and value proposition",
             "A value proposition explains the benefit a product or service offers and why a customer might choose it. It should connect directly to a real need. For example, a collection service may offer reliable scheduled collection to organisations that struggle to manage recyclable materials."),
            ("Customers and delivery channels",
             "A business needs to identify its customer groups and how it will reach them. It may sell directly, use online platforms, work through retailers or partner with institutions. The delivery method should be convenient and suitable for the customer and the product."),
            ("Resources, activities and partners",
             "A model should identify the equipment, people, skills and materials required. It should also explain the activities that must happen regularly. Partners may provide transport, technical expertise, storage, finance or access to customers."),
            ("Costs, income and testing",
             "The model should identify major costs and realistic sources of income. It should be tested with potential customers before large investments are made. A business model is not fixed: evidence, customer feedback and changing conditions may require adjustments.")
        ],
        "action": "Draft a one-paragraph business model describing a problem, a solution, its customers, how it will operate and how it could be financially sustained."
    },

    {
        "title": "Cooperatives and collective enterprise",
        "pillar": PILLARS[2],
        "description": "Understand how people can jointly own and manage an enterprise to pursue shared economic goals.",
        "minutes": 6,
        "content": [
            ("What is a cooperative?",
             "A cooperative is an organisation owned and democratically controlled by members who come together to meet shared economic, social or cultural needs. Cooperatives operate in sectors such as agriculture, finance, housing, retail, energy and recycling."),
            ("Pooling resources and sharing responsibilities",
             "Members may contribute money, labour, equipment, knowledge or access to markets. Working together can improve bargaining power and make some activities more affordable. However, cooperation requires clear responsibilities, reliable communication and agreed rules."),
            ("Democratic member control",
             "Cooperative principles generally emphasise voluntary membership, democratic control, member participation and concern for the community. The exact legal structure differs by country. Members need to understand how decisions are made, how leaders are selected and how financial information is shared."),
            ("Challenges and risks",
             "Cooperatives can face disagreements, weak record-keeping, limited capital, unequal participation and poor management. Shared ownership does not automatically guarantee fairness or success. Transparent procedures and appropriate training help members manage these challenges."),
            ("Collective enterprise in practice",
             "A group of waste collectors, for example, might organise a cooperative to share storage facilities, negotiate with buyers and improve access to equipment. Such a model needs a reliable market, safe working conditions and a fair way of distributing income and responsibilities.")
        ],
        "action": "Imagine a group forming a recycling cooperative. Identify three shared resources and two rules that would help members work fairly."
    },

    {
        "title": "The value of repairing products",
        "pillar": PILLARS[2],
        "description": "Explore how repair extends product life, develops skills and supports circular economic activity.",
        "minutes": 6,
        "content": [
            ("Why repair matters",
             "Repair means restoring a product so that it can continue performing its intended function. It can extend product life, reduce demand for replacement materials and prevent usable items from becoming waste. Repair is often overlooked when products are designed to be difficult or expensive to fix."),
            ("Economic opportunities",
             "Repair services can create work for technicians, craftspeople and small businesses. They may include electronics repair, clothing alterations, bicycle maintenance, furniture restoration and appliance servicing. Demand depends on affordability, trust, access to spare parts and the quality of the repair."),
            ("Repairability and product design",
             "Products are easier to repair when components can be accessed, spare parts are available and repair information is provided. Some products use specialised components or software restrictions that make repair difficult. Consumer organisations and policymakers in different countries have promoted repairability and access to repair information."),
            ("Safety and quality",
             "Not every product should be repaired by an untrained person. Electrical equipment, batteries, gas appliances and safety-critical components can create serious risks if handled incorrectly. Qualified technicians and appropriate safety procedures are important."),
            ("Repair as part of a circular economy",
             "Repair works alongside reuse, refurbishment, remanufacturing and recycling. Keeping a product in use may preserve more of its value than breaking it down for materials. However, repair should be safe, reliable and appropriate for the product's condition.")
        ],
        "action": "Identify one product that is often discarded. Research whether repair is possible, who could do it safely and what might make repair more affordable."
    },

    {
        "title": "Financial planning for small projects",
        "pillar": PILLARS[2],
        "description": "Learn how budgets, estimates and financial records help projects use limited resources responsibly.",
        "minutes": 6,
        "content": [
            ("Why financial planning matters",
             "Financial planning helps a project estimate what it will cost, identify available resources and decide how money should be used. It is important for small community initiatives as well as large organisations. A realistic plan can reveal whether an idea is affordable before commitments are made."),
            ("Building a basic budget",
             "A budget lists expected income and expenditure over a defined period. Costs may include materials, transport, communication, equipment, venue hire, training and maintenance. A budget should explain the quantity and estimated price of each item rather than relying on one unexplained total."),
            ("Estimating and prioritising",
             "Estimates should be based on current prices or reasonable evidence. Projects may need to separate essential costs from optional expenses. If resources are limited, priorities should be linked to the project's objectives and the safety and needs of participants."),
            ("Financial controls and accountability",
             "Good practice includes keeping receipts, recording payments, authorising expenditure appropriately and reconciling records. More than one person may need to review financial information in a group project. Clear controls reduce errors and help prevent misuse."),
            ("Reviewing the budget",
             "Actual costs may differ from estimates because of price changes, delays or unexpected needs. Project teams should compare actual spending with the budget and explain significant differences. Financial planning is an ongoing process, not a document prepared only at the beginning.")
        ],
        "action": "Create a simple budget with at least four cost items for a small community learning or recycling activity."
    },

    {
        "title": "Social entrepreneurship",
        "pillar": PILLARS[2],
        "description": "Explore ventures that address social or environmental challenges while developing sustainable operating models.",
        "minutes": 7,
        "content": [
            ("What social entrepreneurship means",
             "Social entrepreneurship uses entrepreneurial approaches to address social or environmental problems. The central purpose is to create positive impact, while developing a model that can continue operating. Some social enterprises earn income through sales; others combine trading with grants, partnerships or other funding."),
            ("Impact begins with understanding the problem",
             "A social enterprise should identify who experiences the problem, what causes it and why existing solutions are insufficient. It should avoid assuming that a community needs a particular product without consulting the people affected. Research helps ensure that the solution responds to real priorities."),
            ("Balancing mission and money",
             "Social enterprises must consider financial sustainability while protecting their mission. Income may support staff, equipment and service delivery, but financial performance alone does not prove social impact. A venture should be clear about who benefits and how its work creates value."),
            ("Measuring social impact",
             "Impact measurement involves identifying intended changes and collecting evidence about progress. A project might track access to a service, skills gained, materials recovered or improvements in a specific outcome. Indicators should be realistic and should not claim that a project caused changes it cannot demonstrate."),
            ("Ethics and accountability",
             "Social enterprises should treat workers and customers fairly, protect personal information and communicate honestly about results. Communities should have a voice in decisions that affect them. Good intentions do not remove the need for safe practice, competent management and accountability.")
        ],
        "action": "Develop a social enterprise idea. State the problem, the people it aims to serve, how it could earn or receive income and how you would measure its impact."
    },

    {
        "title": "Sustainable business practices",
        "pillar": PILLARS[2],
        "description": "Understand how businesses can consider long-term economic, social and environmental effects.",
        "minutes": 6,
        "content": [
            ("A wider view of business performance",
             "Business success is often measured through income, costs and growth, but businesses also affect workers, customers, communities and the environment. Sustainable business practice considers these effects alongside financial performance and long-term resilience."),
            ("Responsible use of resources",
             "Businesses can reduce unnecessary energy, water and material use, prevent pollution and manage waste responsibly. Resource efficiency may lower operating costs, but improvements should be measured rather than assumed. Some changes require investment before savings become visible."),
            ("People and working conditions",
             "Sustainable practice includes fair treatment, safe working conditions, non-discrimination and respect for workers' rights. Businesses also influence communities through wages, purchasing, local investment and the services they provide."),
            ("Supply chains and responsibility",
             "A product's impact may occur far beyond the shop where it is sold. Raw materials, manufacturing, transport and disposal all matter. Responsible businesses can examine supplier practices, product quality, material sourcing and the risks of harmful labour or environmental practices."),
            ("Avoiding greenwashing",
             "Greenwashing occurs when environmental claims are misleading, exaggerated or unsupported. Businesses should explain what a claim covers, use reliable evidence and acknowledge limitations. Clear reporting builds credibility more effectively than vague statements about being completely green.")
        ],
        "action": "Choose a business you know and suggest one improvement to its environmental practice and one improvement to how it treats people."
    },


    # --------------------------------------------------------
    # TECHNOLOGY, INNOVATION, MEDIA & ARTS — 38 TO 50
    # --------------------------------------------------------

    {
        "title": "Technology for a greener future",
        "pillar": PILLARS[3],
        "description": "Explore how technology can support environmental monitoring, resource efficiency and community solutions.",
        "minutes": 7,
        "content": [
            ("Technology as a tool",
             "Technology includes physical equipment, digital systems, scientific methods and practical techniques. It can help people monitor environmental conditions, manage resources, share information and deliver services. Technology is most useful when it addresses a clearly understood need."),
            ("Examples across sectors",
             "Renewable-energy systems can generate electricity with lower operational emissions than fossil-fuel power. Sensors can monitor air or water conditions. Geographic information systems can map land use and service gaps. Digital platforms can coordinate collection services and connect users with information."),
            ("Technology has limitations",
             "A digital solution may fail if users lack electricity, internet access, affordable devices or digital skills. Sensors can produce inaccurate readings, and software can contain errors. Maintenance, training, data protection and long-term costs must be considered before a technology project is introduced."),
            ("Inclusion and accessibility",
             "Technology should be designed for different users, including people with disabilities and communities with limited connectivity. Offline options, simple interfaces, local languages and accessible support can make a service more useful. Innovation should not deepen inequalities."),
            ("Responsible innovation",
             "A responsible technology project considers safety, privacy, environmental effects, cost and who benefits. It should be tested with users and improved using feedback. A solution should not be described as successful merely because it uses advanced technology.")
        ],
        "action": "Choose an environmental problem and describe one technology that could help. Identify one limitation and one way to make the solution more inclusive."
    },

    {
        "title": "What is digital innovation?",
        "pillar": PILLARS[3],
        "description": "Understand how digital tools can improve services, communication and problem-solving.",
        "minutes": 6,
        "content": [
            ("Defining digital innovation",
             "Digital innovation involves using digital technologies in new or improved ways to create value or solve problems. It may involve a new app, an improved online service, better data systems or a different way of connecting people and organisations."),
            ("Innovation begins with a need",
             "A digital product should begin with a problem worth solving. Developers need to understand users, the environment in which the product will operate and what people currently do to meet the same need. A simple solution that works reliably may be more useful than a complex system."),
            ("From idea to prototype",
             "A prototype is an early version of a product used to explore how an idea might work. It can be a paper design, a basic app or a limited demonstration. Testing a prototype with users helps identify confusing features, missing functions and practical barriers."),
            ("Digital systems and data",
             "Digital services may collect, store and process information. Designers should decide what data is genuinely necessary, who can access it and how it will be protected. Data quality also matters: incorrect information can lead to poor decisions and reduce user trust."),
            ("Innovation and social impact",
             "Digital innovation can support education, health, public services, environmental work and business. However, access is unequal and technology can create new risks. Successful innovation combines useful design with responsible governance, maintenance and user support.")
        ],
        "action": "Describe a simple digital service that could solve a real problem. Identify its main user, its most important function and how you would test it."
    },

    {
        "title": "How QR codes work",
        "pillar": PILLARS[3],
        "description": "Explore how QR codes connect physical objects and locations to digital information.",
        "minutes": 5,
        "content": [
            ("What a QR code is",
             "A QR code is a two-dimensional barcode that stores information in a pattern of squares. A smartphone camera or QR-scanning application can read the pattern and interpret the information. QR codes can contain text or provide a link to online content."),
            ("How scanning works",
             "The scanning device detects the code's pattern and decodes the information stored in it. If the code contains a web address, the device may offer to open that address. The user should check that the destination is trustworthy before proceeding."),
            ("Practical applications",
             "QR codes can link to educational materials, event registration, product information, digital menus, feedback forms and instructions. In environmental projects, they might provide information about a tree, explain how to sort materials or direct people to a collection-point map."),
            ("Security and privacy",
             "A QR code can lead to an unsafe or misleading website just as a normal link can. Users should be cautious with unexpected codes, check the destination where possible and avoid entering passwords or personal information into unfamiliar pages. Organisations should use trusted links and keep destinations updated."),
            ("Good design and accessibility",
             "A QR code should be large enough to scan, printed clearly and placed where users can access it safely. It should not be the only way to obtain important information because some people may not have a smartphone, data or the ability to scan it. A readable web address or printed explanation can provide an alternative.")
        ],
        "action": "Design a simple QR-code information idea for a learning space or environmental project. Explain what the code should open and how people without smartphones could access the same information."
    },

    {
        "title": "Why environmental data matters",
        "pillar": PILLARS[3],
        "description": "Learn how reliable data helps identify problems, guide decisions and measure environmental progress.",
        "minutes": 6,
        "content": [
            ("What environmental data includes",
             "Environmental data can include measurements and observations about air quality, water, rainfall, temperature, biodiversity, land use, waste and energy. It may come from monitoring stations, surveys, satellites, field observations or administrative records."),
            ("Evidence supports decisions",
             "Data can help identify where a problem is concentrated, whether conditions are changing and which groups may be affected. For example, records of waste collection can reveal service gaps, while water-quality measurements can help identify possible pollution concerns."),
            ("Quality matters",
             "Data is useful only when it is collected and interpreted carefully. Important questions include who collected it, when and where it was collected, what method was used and whether measurements are complete. Incorrect or inconsistent records can produce misleading conclusions."),
            ("Turning information into action",
             "Data should connect to a decision or question. A project may collect information about the amount of material recovered, but it should also explain how the information will be used. Charts and dashboards can make patterns easier to see, but they do not replace careful interpretation."),
            ("Ethics and responsible data use",
             "Environmental projects may also collect information about people, households or locations. Personal data should be protected, unnecessary collection avoided and access restricted. Public reports should explain limitations and avoid exaggerating what the data proves.")
        ],
        "action": "Choose an environmental project and identify three pieces of information it should record, how each would be collected and what decision the information could support."
    },

    {
        "title": "Digital literacy",
        "pillar": PILLARS[3],
        "description": "Develop the skills to use digital devices, information and online services safely and effectively.",
        "minutes": 6,
        "content": [
            ("What digital literacy means",
             "Digital literacy is the ability to use digital devices, services and information effectively, safely and responsibly. It includes more than knowing how to operate a phone or computer. It also involves searching for information, communicating, evaluating content and understanding digital risks."),
            ("Finding and evaluating information",
             "Online search results may include reliable research, advertisements, outdated information and misleading claims. Users should check who published the information, when it was published, what evidence supports it and whether other trustworthy sources agree."),
            ("Communication and digital citizenship",
             "Digital communication requires respect, clarity and awareness of context. People should avoid harassment, impersonation and sharing private information without permission. Disagreement online should be handled responsibly, just as it should be in face-to-face settings."),
            ("Practical digital skills",
             "Useful skills include creating documents, managing files, using online forms, recognising secure websites, organising information and solving basic technical problems. Skills improve through practice and should be matched to the tasks people need to perform."),
            ("The digital divide",
             "Access to devices, electricity, affordable data, connectivity and accessible software differs across communities and countries. Digital services should consider people who are offline or have limited digital skills. Providing an online service does not automatically make a service accessible to everyone.")
        ],
        "action": "Choose an online claim or article and list the steps you would use to check its source, date and evidence before relying on it."
    },

    {
        "title": "Data privacy and online safety",
        "pillar": PILLARS[3],
        "description": "Understand how personal information can be exposed online and how digital services should protect users.",
        "minutes": 7,
        "content": [
            ("What personal data means",
             "Personal data is information that identifies or can be linked to an individual. It may include names, contact details, photographs, account information, location information and other identifiers. Some information is particularly sensitive and requires stronger protection."),
            ("How digital information can be exposed",
             "Information may be exposed through weak passwords, phishing messages, unsafe links, lost devices, excessive app permissions or poorly secured databases. Data can also be shared by users themselves without understanding who may see it or how long it may remain available."),
            ("Good habits for users",
             "Users should use strong, unique passwords where possible, protect account access, be cautious with unexpected links and keep devices and applications updated. They should think carefully before sharing personal details, photographs or location information publicly."),
            ("Responsibilities of organisations",
             "Organisations should collect only information they genuinely need, explain why it is collected, limit access, secure stored information and establish procedures for handling incidents. Privacy should be considered when a digital service is designed, not added only after a problem occurs."),
            ("Trust and responsible technology",
             "People are more likely to use digital services when they understand how their information is handled. Clear privacy information, secure systems, fair access controls and responsible staff practices help build trust. No system is risk-free, so organisations should review and improve their safeguards.")
        ],
        "action": "Review the information a hypothetical community app might request. Identify which details are necessary, which are unnecessary and how the necessary information should be protected."
    },

    {
        "title": "Citizen science",
        "pillar": PILLARS[3],
        "description": "Discover how members of the public can contribute observations and data to scientific work.",
        "minutes": 6,
        "content": [
            ("What citizen science means",
             "Citizen science involves members of the public contributing to scientific research. Participants may record observations, classify images, monitor local environments or help collect data. Activities can be organised by universities, research institutions, museums, public agencies or community groups."),
            ("Why public participation is valuable",
             "Researchers may not have enough resources to observe every location or collect information over long periods. Community participation can expand the geographic reach and frequency of observations. It can also help people understand scientific methods and environmental issues."),
            ("Examples around the world",
             "Citizen-science projects may monitor birds, record rainfall, map invasive species, observe insects, report pollution or classify images from scientific databases. Some projects use smartphone applications, while others use paper forms or organised field activities."),
            ("Reliable methods matter",
             "Participants need clear instructions about what to observe, how to record it and how to submit information. Training and verification help reduce errors. Researchers should explain limitations and avoid treating every observation as equally reliable without checking the method and context."),
            ("Ethics and inclusion",
             "Projects should consider participant safety, informed participation, privacy and the rights of communities. Not everyone has a smartphone or internet access, so different participation methods may be needed. Contributors should also understand how their data may be used and acknowledged.")
        ],
        "action": "Design a simple citizen-science activity that records one environmental observation. State what participants would record and how the information would be checked."
    },

    {
        "title": "Environmental storytelling",
        "pillar": PILLARS[3],
        "description": "Explore how stories, images and lived experiences can communicate environmental issues responsibly.",
        "minutes": 6,
        "content": [
            ("What environmental storytelling does",
             "Environmental storytelling uses written stories, photographs, film, audio, art and other media to help people understand relationships between communities and the natural world. It can make complex issues more relatable by connecting evidence with real experiences."),
            ("Connecting evidence and experience",
             "A powerful story can show how an environmental issue affects livelihoods, health, culture or daily routines. However, personal experiences should be presented alongside accurate information where factual claims are made. A moving story should not replace evidence or misrepresent the causes of a problem."),
            ("Representation and dignity",
             "People featured in environmental stories should be treated with respect. Creators should seek appropriate permission, avoid humiliating images and consider whether publishing a person's identity or location could create risk. Communities should not be portrayed only as helpless victims."),
            ("Choosing a useful format",
             "Different formats serve different purposes. A short video may show a changing landscape, a photo essay may document a clean-up, a podcast may explore community perspectives and an infographic may explain a process. The format should match the audience, message and available resources."),
            ("From awareness to action",
             "Storytelling can encourage learning and participation, but awareness alone does not solve environmental problems. Useful stories help audiences understand the issue, identify responsible actors and see realistic ways to contribute or seek change.")
        ],
        "action": "Outline a short environmental story with a clear issue, a human perspective, one verified fact and a constructive message."
    },

    {
        "title": "Media literacy and misinformation",
        "pillar": PILLARS[3],
        "description": "Learn how to evaluate media messages, identify misleading claims and share information responsibly.",
        "minutes": 7,
        "content": [
            ("What media literacy means",
             "Media literacy is the ability to access, analyse, evaluate and create media messages. It helps people understand how information is produced, why it is shared and how images, headlines, editing and language can influence interpretation."),
            ("Misinformation and disinformation",
             "Misinformation is false or inaccurate information shared without necessarily intending to deceive. Disinformation is false information deliberately created or shared to mislead. Both can spread quickly through social media, messaging platforms and other communication channels."),
            ("How misleading content works",
             "Misleading content may use old photographs as if they were recent, remove important context, exaggerate statistics or present opinion as established fact. A headline may not accurately represent the full article. Images and videos can also be edited or generated in ways that make verification difficult."),
            ("A practical verification process",
             "Check the original source, publication date, author, evidence and context. Search for the same claim in other reliable sources. For photographs, consider whether the image has appeared elsewhere or been used in a different context. Be cautious when a message pressures you to share immediately."),
            ("Responsible sharing",
             "People can reduce the spread of false information by pausing before forwarding, correcting mistakes respectfully and distinguishing confirmed facts from uncertainty. If a claim could affect health, safety or public decisions, stronger verification is especially important.")
        ],
        "action": "Choose a claim about an environmental issue and describe how you would verify its source, date, context and supporting evidence."
    },

    {
        "title": "Introduction to artificial intelligence",
        "pillar": PILLARS[3],
        "description": "Understand what AI systems do, where they are used and why human judgement remains important.",
        "minutes": 7,
        "content": [
            ("What artificial intelligence means",
             "Artificial intelligence refers to computer systems designed to perform tasks commonly associated with human intelligence, such as recognising patterns, processing language, generating content or making predictions. Different AI systems use different methods and are suited to different tasks."),
            ("How many AI systems learn patterns",
             "Many modern AI systems are developed using data and mathematical methods that identify patterns. A model may be trained on examples and then used to make predictions or generate outputs. The quality of those outputs depends on factors such as the data, design, testing and task."),
            ("Uses across society",
             "AI is used in areas such as language translation, image recognition, transport planning, customer support, scientific research and environmental monitoring. It may help analyse large datasets or identify patterns that would be difficult to review manually."),
            ("Limitations and risks",
             "AI systems can produce inaccurate, incomplete or misleading outputs. They may reflect biases in their training data, fail in unfamiliar situations or make errors that sound confident. Some systems also raise concerns about privacy, intellectual property, employment and unequal access."),
            ("Responsible human oversight",
             "AI should be used with an understanding of its limitations. Important decisions should involve appropriate human review, reliable evidence and accountability. Users should avoid entering sensitive personal information into tools unless they understand how it is handled, and should verify important outputs independently.")
        ],
        "action": "Identify one task where AI could support an environmental project. Explain what a human should check before acting on the AI's output."
    },

    {
        "title": "Mapping technology for communities",
        "pillar": PILLARS[3],
        "description": "Explore how digital and community mapping can support planning, services and environmental monitoring.",
        "minutes": 6,
        "content": [
            ("What mapping technology does",
             "Digital mapping uses geographic information to represent places, routes, boundaries and features. Geographic information systems can combine location data with other information, such as population, roads, land use, public services or environmental conditions."),
            ("Applications in community development",
             "Maps can help identify where public services are located, which areas lack access and where infrastructure may be under pressure. Environmental projects may map waste collection points, flood-prone areas, water sources, tree cover or locations where pollution has been reported."),
            ("Community mapping and local knowledge",
             "Residents may contribute information about places that are missing from official datasets or difficult to observe remotely. Participatory mapping can help communities describe local priorities, but the process should respect land rights, cultural knowledge and disagreements about boundaries or resource use."),
            ("Accuracy and interpretation",
             "A map is only as reliable as its data and methods. Location errors, outdated information and incomplete coverage can mislead users. Maps can also create a false impression of certainty, so dates, sources and limitations should be made clear."),
            ("Privacy and responsible sharing",
             "Some locations should not be publicly exposed, including sensitive personal locations, vulnerable wildlife sites or information that could create safety risks. Mapping projects should decide what information is necessary, who can access it and whether precise locations should be restricted.")
        ],
        "action": "Choose a community service or environmental issue that could be mapped. Identify the information needed and one privacy or accuracy risk to consider."
    },

    {
        "title": "Design thinking and problem-solving",
        "pillar": PILLARS[3],
        "description": "Learn a human-centred process for understanding needs, testing ideas and improving solutions.",
        "minutes": 7,
        "content": [
            ("What design thinking is",
             "Design thinking is an approach to problem-solving that places people's needs at the centre of the design process. It encourages teams to understand users, define a clear problem, explore possible ideas, create prototypes and test them before making wider commitments."),
            ("Understand people first",
             "The process begins by learning about the people who experience the problem. Interviews, observation and discussions can reveal needs that are not obvious from a distance. Designers should avoid assuming that they already know what users want."),
            ("Define the real problem",
             "A clear problem statement helps a team focus. It should describe who experiences the issue, what difficulty they face and why it matters. A poorly defined problem can lead to a technically impressive solution that does not address the actual need."),
            ("Generate and test ideas",
             "Teams can develop several possible solutions before choosing one to prototype. A prototype may be a sketch, model, paper interface or basic working product. Testing should invite honest feedback and reveal what needs to change."),
            ("Iteration and responsible design",
             "Design thinking is iterative: teams learn from testing and improve the solution. A design should also consider affordability, accessibility, safety, privacy, maintenance and environmental effects. A successful prototype still needs further testing before large-scale use.")
        ],
        "action": "Choose a problem affecting a group of users. Write a problem statement, suggest two possible solutions and describe how you would test one of them."
    },

    {
        "title": "Arts, creativity and climate action",
        "pillar": PILLARS[3],
        "description": "Discover how creative expression can communicate environmental ideas and encourage participation.",
        "minutes": 6,
        "content": [
            ("Creativity as a form of communication",
             "Music, theatre, dance, photography, film, fashion, visual arts and design can communicate environmental ideas in ways that reach different audiences. Creative work can make complex issues easier to discuss and can connect environmental concerns with culture, identity and everyday life."),
            ("Art can invite participation",
             "Creative activities can bring people together through exhibitions, performances, public murals, storytelling events and community campaigns. Participation can help people express their experiences and imagine different futures. Projects should be designed with communities rather than simply using them as an audience."),
            ("Combining creativity with evidence",
             "Creative communication is strongest when factual claims are accurate. A poster or performance may simplify a complex issue, but it should not distort scientific evidence or spread fear through unsupported claims. Creators can use reliable sources while still making space for emotion and imagination."),
            ("Culture and local knowledge",
             "Environmental art can reflect local languages, histories, knowledge systems and relationships with land and nature. Different communities may express environmental values in different ways. Respectful creative work avoids copying cultural expressions without permission or presenting one culture as representative of everyone."),
            ("Measuring engagement and impact",
             "A campaign can record participation, audience feedback, learning outcomes or follow-up activities. Attendance alone does not prove that attitudes or behaviour changed. Evaluation should consider what the creative activity achieved and what could be improved.")
        ],
        "action": "Design a creative campaign idea about an environmental issue. Choose a format, identify its audience and explain one message you want people to understand."
    }

]


# ============================================================
# 3. BUILD THE LESSON LIST
# Keep the original lesson IDs so existing completion records
# continue to match the same learning materials.
# ============================================================

LESSONS = []

for index, item in enumerate(READING_TOPICS, start=1):
    LESSONS.append({
        "id": f"eco_{index:03d}",
        "title": item["title"],
        "category": item["pillar"],
        "pillar": item["pillar"],
        "minutes": item["minutes"],
        "description": item["description"],
        "content": item["content"],
        "action": item["action"]
    })
    # ============================================================
# 4. TIME DISPLAY
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
                value = value.astimezone(
                    ZoneInfo(timezone_name)
                )
            except (ZoneInfoNotFoundError, ValueError):
                value = value.astimezone(timezone.utc)
        else:
            value = value.astimezone(timezone.utc)

        return value.strftime("%d %b %Y · %I:%M %p")

    except Exception:
        return str(timestamp)


# ============================================================
# 5. GENERAL HELPERS
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

                st.write(
                    comment.get("comment", "")
                )

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
        st.warning(
            f"Could not load approved groups: {e}"
        )
        return []


def _group_selector(
    supabase,
    user_id,
    user_name,
    key
):
    groups = _get_approved_groups(
        supabase,
        user_id
    )

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
# 6. UNIVERSAL POINTS — LESSON COMPLETION
# ============================================================

def _award_learning_points(
    supabase,
    user_id,
    group_id,
    lesson_id
):
    description = (
        f"Explore & Learn lesson completed: {lesson_id}"
    )

    try:
        existing = (
            supabase.table("point_transactions")
            .select("id")
            .eq("user_id", user_id)
            .eq("activity_type", "learning_completion")
            .eq("description", description)
        )

        if group_id:
            existing = existing.eq(
                "group_id",
                group_id
            )
        else:
            existing = existing.is_(
                "group_id",
                "null"
            )

        result = existing.limit(1).execute()

        if result.data:
            return False

        supabase.table(
            "point_transactions"
        ).insert({
            "user_id": user_id,
            "group_id": group_id,
            "activity_type": "learning_completion",
            "points": 5,
            "description": description
        }).execute()

        return True

    except Exception as e:
        st.warning(
            "The lesson was recorded, but points could "
            f"not be confirmed: {e}"
        )
        return False


# ============================================================
# 7. DISCOVER — LEARNING LIBRARY
# ============================================================

def _reading_library(
    supabase,
    user_id,
    group_id,
    user_name,
    timezone_name=None
):
    st.subheader("📚 Discover")

    st.write(
        "Explore 50 expanded learning materials across "
        "the four NGIH pillars. Learn about global issues, "
        "discover different perspectives and connect "
        "knowledge to practical action."
    )

    activity_group_id, activity_group_name = (
        _group_selector(
            supabase,
            user_id,
            user_name,
            "learning_group_choice"
        )
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

            st.markdown(
                f"## {lesson['title']}"
            )

            st.caption(
                f"{lesson['category']} · "
                f"{lesson['minutes']} minute read"
            )

            st.write(lesson["description"])

            st.divider()

            for heading, paragraph in lesson["content"]:
                st.markdown(f"### {heading}")
                st.write(paragraph)

            st.divider()

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
                            supabase.table(
                                "learning_completions"
                            )
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
                            supabase.table(
                                "learning_completions"
                            ).insert({
                                "user_id": user_id,
                                "group_id": activity_group_id,
                                "lesson_id": lesson["id"]
                            }).execute()

                            awarded = _award_learning_points(
                                supabase,
                                user_id,
                                activity_group_id,
                                lesson["id"]
                            )

                            st.success(
                                "Lesson completion recorded!"
                            )

                            if awarded:
                                st.success(
                                    "🌱 5 universal points awarded!"
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

    visible_lessons = lessons[
        start_index:end_index
    ]

    if not visible_lessons:
        st.info(
            "No learning materials match your search."
        )
        return

    for lesson in visible_lessons:
        with st.container(border=True):
            st.markdown(
                f"### {lesson['title']}"
            )

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
            f"{min(end_index, len(lessons))} "
            f"of {len(lessons)}"
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
# 8. RESOURCE LIBRARY AND MEMBER UPLOADS
# ============================================================

def _resource_library(
    supabase,
    user_id,
    is_coordinator
):
    st.subheader("🌍 Reading & Resource Library")

    st.write(
        "Explore approved learning resources shared "
        "by the EcoLoop community. Members can also "
        "submit useful materials for review."
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

    st.markdown(
        "### 📤 Contribute a learning resource"
    )

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
# 9. COORDINATOR RESOURCE APPROVAL
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
# 10. MAIN EXPLORE & LEARN PAGE
# ONLY TWO TABS:
# DISCOVER + RESOURCE LIBRARY
# NO QUIZ TAB OR QUIZ RENDERING FUNCTION
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
        "🌍 Explore global knowledge, discover new ideas, "
        "understand different perspectives and turn learning "
        "into meaningful action."
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

    # IMPORTANT:
    # Eco Quizzes is a separate section in the main app.
    # Do not add a quiz tab or call a quiz-rendering function here.

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
