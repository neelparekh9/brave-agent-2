export const conversationMap = {
  initial: {
    agentResponse: "Hello, I am here to help. What is on your mind?",
    nextOptions: [
      { text: "I’m stressed about…", next: "intro" },
      { text: "I’m worried about…", next: "intro" },
      { text: "I don’t feel supported to…", next: "intro" },
      { text: "I don’t want to feel desperate about…", next: "intro" }
    ],
    animation: ["Idle"]
  },

  intro: {
    agentResponse: "You are not alone! This app / I am here to help you navigate through hard times, and what I know for sure is that we are most healthy and happy when our relationships are healthy and happy. \n\nBut I know sometimes it is hard, in fact sometimes it feels impossible. \n\nWelcome to the Brave Dialog app. Together, we are going to find solutions to your concerns.",
    nextOptions: [{ text: "Where do I start?", next: "zeroNegativity" }],
    animation: ["handup", "Idle"]
  },

  zeroNegativity: {
    agentResponse: "The starting point whenever you feel stressed/anxious/scared (whatever) is to think about your own attitude. \n\nYou have a choice! To be negative and shut down, or to open up to possibility. We call this PRACTICING ZERO NEGATIVITY.",
    nextOptions: [{ text: "What’s that?", next: "zeroNegativityDetails" }],
    animation: ["ok", "Idle"],
    audioUrl: "/audio/intro2.mp3"
  },

  zeroNegativityDetails: {
    agentResponse: "Zero Negativity is a simple promise to approach others with openness. ",
    nextOptions: [{ text: "I WILL PRACTICE ZERO NEGATIVITY FOR ONE FULL DAY!", next: "zeroNegativityQuestions" }],
    animation: ["ok", "handup"]
  },

  // \n\nInstead of being defensive and snapping back, ask this question: “What do you mean by that?”\n\nInstead of rolling your eyes or walking away, make eye contact or smile. \n\nTo get you started, give yourself a challenge that you will practice Zero Negativity for one full day. Simply say “I will” at the end of this statement:  \n\nI will avoid criticizing others and putting them down. When I do get negative, or when I experience negativity, I will raise my hand and request that we start over in Zero Negativity.

  zeroNegativityQuestions: {
    agentResponse: "Now, let’s start the Zero Negativity Practice. I’ll bet you have questions.",
    nextOptions: [
      { text: "How can I practice Zero Negativity if others do not?", next: "zeroNegativityContagious" },
      { text: "What do I say when others are negative?", next: "zeroNegativityResponse" }
    ],
    animation: ["Idle"]
  },

  zeroNegativityContagious: {
    agentResponse: "Zero Negativity is contagious. If you can practice some simple actions, you will find that others mirror you. Try this:\n\nUse “I” messages instead of “You”. Like: “I feel left out when you stay out late” instead of “You always stay out late!”\n\nWhy? Because when people hear the word “YOU” they think you’re criticizing them, and they tune out or they push back.\n\nTry stating your frustration using an “I” message now:",
    nextOptions: [{ text: "Next", next: "appreciation" }],
    animation: ["ok"]
  },

  appreciation: {
    agentResponse: "Offering an appreciation to someone is the number one way to create Zero Negativity. \n\nYou feel good when you tell someone what you like about them or do something for them that they need - and they feel good when they receive these things from you. \n\nWhy? Appreciations make people feel validated, and they feel safe in your interactions. When you feel validated by someone, you feel free to collaborate and problem solve together.",
    nextOptions: [{ text: "Give me some examples of Appreciations.", next: "appreciationExamples" }],
    animation: ["ok"]
  },

  appreciationExamples: {
    agentResponse: "You can appreciate someone in many ways: ask if you can help them do a task, give a small gift or token, have a laugh with them or be specific and offer an Appreciation in words.",
    nextOptions: [{ text: "When someone is stressed out and negative, how do I interrupt to offer an Appreciation? ", next: "appreciationInterruption" }],
    animation: ["ok"]

  },
  appreciationInterruption: {
    agentResponse: "Start by saying: “Is now a good time to tell you something I appreciate about you?” If now is not a good time, then ask: “When can I come back? I really want to have this conversation with you.” I promise, this will be a surprise, and people always want to hear good news!",
    nextOptions: [{ text: "Sometimes I wish I could hear what someone appreciates about me. Especially when I’m frustrated. ", next: "frustrationIntro" }],
  },

  frustrationIntro: {
    agentResponse: "When you get frustrated about something, it is your responsibility to share about it. Why? Because if you don’t communicate no one knows how you feel! They can’t read your mind! This is called Dialogue. When you share your ideas, opinions or frustrations with someone so they can help you problem solve.",
    nextOptions: [{ text: "How do I do that?", next: "frustrationSharing" }],
    animation: ["ok", "handup"]
  },

  frustrationSharing: {
    agentResponse: "When you practice Zero Negativity, having safe conversations is not a confrontation or a fight, it’s a way of making the situation better.\n\nImagine turning your frustration into a wish for change. That means instead of dwelling on what frustrates you, think about what you’d rather have instead.",
    nextOptions: [{ text: "When I’m frustrated, the last thing I want to do is have a conversation.", next: "frustrationStart" }],
    animation: ["ok"]
  },

  frustrationStart: {
    agentResponse: "That makes sense. But if you keep frustrations to yourself, they will fester and grow and erupt into anger. When that happens it’s hard to even know what you are frustrated about.\n\nLet’s see if we can make talking about your frustrations easier.",
    nextOptions: [{ text: "Where do I start?", next: "frustrationSteps" }],
    animation: ["ok"]
  },

  frustrationSteps: {
    agentResponse: "Follow this road map when you tell someone what’s frustrating you. Start first with ‘Is now a good time to tell you about a frustration I’m having.’ This way you know the person you’re talking to is ready to listen.\n\nIs now a good time to talk about something that’s frustrating me?\n\nI get frustrated when…\n\nAnd I feel…\n\nAnd it reminds me of a time in the past when…\n\nInstead of this frustration, I wish for…..\n\nDoes this make sense to you? And if so, can we work together to create a solution?",
    nextOptions: [{ text: "How will I remember this?", next: "frustrationMemory" },
    { text: "And what if the person I’m talking to gets mad?", next: "frustrationConflict" }],
    animation: ["ok"]
  },

  frustrationMemory: {
    agentResponse: "Just remember to turn your frustration into a wish. Start with what is frustrating you then turn it around.\n\nI’m frustrated about….\nAnd I wish for…..\n\nIt’s that simple. Then you can add in how you feel and what you’re reminded about. You can always come back to this page when you get stuck.\n\nTry it here. Follow the prompts and practice a conversation about something that frustrates you.",
    nextOptions: [{ text: "Next", next: "end" }],
    animation: ["ok"]
  },

  frustrationConflict: {
    agentResponse: "Remember ZERO NEGATIVITY. Always start your statements with I. ‘I am frustrated because…’ Never ‘YOU frustrate me when you….’\n\nAnd if it’s not a good time for the other person to listen, set a time to talk later. It’s important to respect their availability!",
    nextOptions: [{ text: "Next", next: "end" }],
    animation: ["ok"]
  },

  end: {
    agentResponse: "Thank you for engaging in this conversation! Would you like to restart or exit?",
    nextOptions: [
      { text: "Restart", action: { type: "RESET" } },
      { text: "Exit", action: { type: "EXIT" } }
    ],
    isEnd: true,
    animation: ["handup", "Idle"]
  }
};