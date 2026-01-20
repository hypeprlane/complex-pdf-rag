USER_QUESTION_DECOMPOSITION_PROMPT = """
You are an expert assistant that breaks down complex technical questions related to a machine manual. Your goal is to enhance the reasoning ability of downstream models by decomposing the user's question into sub-questions that progressively build understanding, cover all necessary concepts, and help derive complex conclusions.

You have access to the structure of the manual below, including sections and chapters. Use this structure to anchor each sub-question in the most relevant content.

Manual Structure:

[
  {{
    "section": 1,
    "title": "Safety Practices",
    "chapters": [
      "Introduction", "Disclaimer", "Operation & Safety Manual", "Do Not Operate Tags",
      "Safety Information", "Safety Instructions", "Safety Decals"
    ]
  }},
  {{
    "section": 2,
    "title": "General Information and Specifications",
    "chapters": [
      "Replacement Parts and Warranty Information", "Specifications", "Fluid and Lubricant Capacities",
      "Service and Maintenance Schedules", "Lubrication Schedule", "Thread Locking Compound",
      "Torque Charts", "Hydraulic Connection Assembly and Torque Specification"
    ]
  }},
  {{
    "section": 3,
    "title": "Boom",
    "chapters": [
      "Boom System Component Terminology", "Boom System", "Boom Removal/Installation",
      "Boom Assembly Maintenance - 642, 742, 943, 1043", "Third Boom Section Removal/Installation Only - 642, 742, 943, 1043",
      "Boom Assembly Maintenance - 1055, 1255", "Fourth Boom Section Removal/Installation Only - 1055, 1255",
      "Hose Carrier Assembly - 1055, 1255", "Boom Sections Adjustment - 642, 742, 943, 1043",
      "Boom Sections Adjustment - 1055, 1255", "Boom Extend and Retract Chains", "Boom Wear Pads",
      "Quick Coupler", "Forks", "Emergency Boom Lowering Procedure", "Troubleshooting"
    ]
  }},
  {{
    "section": 4,
    "title": "Cab",
    "chapters": [
      "Operator Cab Component Terminology", "Operator Cab", "Cab Components",
      "Cab Removal", "Cab Installation"
    ]
  }},
  {{
    "section": 5,
    "title": "Axles, Drive Shafts, Wheels and Tires",
    "chapters": [
      "Axle, Drive Shaft and Wheel Component Terminology", "Axle Serial Number",
      "Axle Specifications and Maintenance Information", "Axle Replacement", "Brake Inspection",
      "Steering Angle Adjustment", "Axle Assembly and Drive Shaft Troubleshooting",
      "Drive Shafts", "Wheels and Tires", "Towing a Disabled Machine"
    ]
  }},
  {{
    "section": 6,
    "title": "Transmission",
    "chapters": [
      "Transmission Assembly Component Terminology", "Transmission Serial Number",
      "Specifications and Maintenance Information", "Transmission Replacement",
      "Transmission Fluid/Filter Replacement", "Transmission Fluid Level Check",
      "Transmission Cooler Thermal By-Pass Valve", "Torque Converter Diaphragm"
    ]
  }},
  {{
    "section": 7,
    "title": "Engine",
    "chapters": [
      "Introduction", "Engine Serial Number", "Specifications and Maintenance Information",
      "Engine Cooling System", "Engine Electrical System", "Fuel System", "Engine Exhaust System",
      "Air Cleaner Assembly", "Engine Replacement", "Troubleshooting"
    ]
  }},
  {{
    "section": 8,
    "title": "Hydraulic System",
    "chapters": [
      "Hydraulic Component Terminology", "Safety Information", "Specifications",
      "Hydraulic Pressure Diagnosis", "Hydraulic Circuits", "Hydraulic Schematic",
      "Hydraulic Reservoir", "Implement Pump", "Control Valves", "Rear Axle Stabilization (RAS) System",
      "Precision Gravity Lower System (PGLS)", "Boom Ride Control", "Hydraulic Cylinders"
    ]
  }},
  {{
    "section": 9,
    "title": "Electrical System",
    "chapters": [
      "Electrical Component Terminology", "Specifications", "Safety Information",
      "Power Distribution Boards", "Electrical System Schematics", "Electrical Grease Application",
      "Engine Start Circuit", "Battery", "Electrical Master Switch", "Window Wiper System (if equipped)",
      "Solenoids, Sensors and Senders", "Dash Switches", "Machine Data", "Analyzer Software Accessibility",
      "Telematics Gateway", "Multifunction Display", "Fault Codes", "Machine Fault Codes", "Engine Diagnostic"
    ]
  }}
]

User Question:
{user_question}

Instructions:

1. Carefully analyze the question to identify key concepts, comparisons, dependencies, specifications, and implications.

2. Decompose the question into maximum 4 **reasoning-enhancing sub-questions**. These sub-questions should help a language model understand the topic progressively. Consider including:
   - Fact-finding sub-questions (specifications, definitions, values)
   - Comparative sub-questions (model differences, implications)
   - Causal or inferential sub-questions (how one property affects another)
   - Contextual or procedural sub-questions (what this means for usage, maintenance, safety)

3. Each sub-question must be:
   - Answerable using the manual
   - As atomic and logically coherent as possible
   - Mapped to the **correct section number, section title, and list of chapters** from the manual

4. Return only the JSON array in the following format:

[
  {{
    "sub_question": "What are the front axle differential housing capacities for models 943 and 1255?",
    "section_number": 2,
    "section_title": "General Information and Specifications",
    "matched_chapters": ["Fluid and Lubricant Capacities"]
  }},
  {{
    "sub_question": "What are the rear axle differential housing capacities for models 943 and 1255?",
    "section_number": 2,
    "section_title": "General Information and Specifications",
    "matched_chapters": ["Fluid and Lubricant Capacities"]
  }},
  {{
    "sub_question": "How does the difference in axle fluid capacity between models 943 and 1255 affect lubrication frequency?",
    "section_number": 2,
    "section_title": "General Information and Specifications",
    "matched_chapters": ["Lubrication Schedule", "Service and Maintenance Schedules"]
  }},
  {{
    "sub_question": "How does total lubricant volume influence the overall maintenance plan for front and rear axles?",
    "section_number": 2,
    "section_title": "General Information and Specifications",
    "matched_chapters": ["Service and Maintenance Schedules"]
  }},
  {{
    "sub_question": "Are there any structural or mechanical differences in axle housings between models 943 and 1255 that explain fluid capacity differences?",
    "section_number": 5,
    "section_title": "Axles, Drive Shafts, Wheels and Tires",
    "matched_chapters": ["Axle Specifications and Maintenance Information"]
  }}
]

Only return the JSON array. Do not explain or include any additional text or formatting.
"""
