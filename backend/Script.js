module.exports = {
  initial: {
    agentResponse: "Hello, I am here to help. What is on your mind?",
    nextOptions: [
      { text: "I'm stressed about...", next: "intro" },
      { text: "I'm worried about...", next: "intro" },
      { text: "I don't feel supported to...", next: "intro" },
      { text: "I don't want to feel desperate about...", next: "intro" }
    ],
    animation: ["Idle"]
  },

  intro: {
    agentResponse: "You are not alone! This app or I am here to help you navigate through hard times, and what I know for sure is that we are most healthy and happy when our relationships are healthy and happy. But I know sometimes it is hard, in fact sometimes it feels impossible. Welcome to the Safe Conversations app. Together, we are going to find solutions to your concerns.",
    nextOptions: [{ text: "Where do I start???", next: "zeroNegativity" }],
    animation: ["handup", "Idle"]
  },

  zeroNegativity: {
    agentResponse: "The starting point whenever you feel stressed, anxious, or scared is to think about your own attitude. You have a choice! To be negative and shut down, or to open up to possibility. We call this PRACTICING ZERO NEGATIVITY.",
    nextOptions: [{ text: "What's that?", next: "zeroNegativityDetails" }],
    animation: ["ok", "Idle"]
  },

  zeroNegativityDetails: {
    agentResponse: "Zero Negativity is a simple promise to approach others with openness. Instead of being defensive and snapping back, ask this question: 'What do you mean by that?' Instead of rolling your eyes or walking away, make eye contact or smile. To get you started, give yourself a challenge that you will practice Zero Negativity for one full day. Simply say 'I will' at the end of this statement: I will avoid criticizing others and putting them down. When I do get negative, or when I experience negativity, I will raise my hand and request that we start over in Zero Negativity.",
    nextOptions: [{ text: "I WILL PRACTICE ZERO NEGATIVITY FOR ONE FULL DAY!", next: "zeroNegativityQuestions" }],
    animation: ["ok", "handup"]
  },

  zeroNegativityQuestions: {
    agentResponse: "Now, let's start the Zero Negativity Practice. I'll bet you have questions.",
    nextOptions: [
      { text: "Restart", action: { type: "RESET" } }
    ],
    animation: ["Idle"]
  }
};
