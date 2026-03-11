import React, { useEffect } from "react";
import { conversationMap } from "../data/Script.js";
import { TalkingHead } from "../libs/talkinghead.js";


const GOOGLE_TTS_API_KEY = process.env.REACT_APP_GOOGLE_TTS_API_KEY;

const fetchGoogleTTS = async (text) => {
    if (!text || typeof text !== "string") {
      console.error("❌ fetchGoogleTTS Error: Text is undefined or not a string.", text);
      return null; // ✅ Prevents further execution if text is invalid
    }
  
    const url = `https://texttospeech.googleapis.com/v1/text:synthesize?key=${process.env.REACT_APP_GOOGLE_TTS_API_KEY}`;
  
    const requestBody = {
      input: { text: text.trim() }, // ✅ Trim only if text is valid
      voice: {
        languageCode: "en-US",
        name: "en-US-Wavenet-D",
        ssmlGender: "NEUTRAL"
      },
      audioConfig: {
        audioEncoding: "MP3",
        speakingRate: 1.0,
        pitch: 0
      }
    };
  
    try {
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody)
      });
  
      const data = await response.json();
      if (data.audioContent) {
        return `data:audio/mp3;base64,${data.audioContent}`;
      } else {
        console.error("❌ Google TTS API Error Response:", data);
      }
    } catch (error) {
      console.error("❌ Google TTS API Request Failed:", error);
    }
  
    return null;
  };
  
  

const AudioHandler = ({ currentNode }) => {
  useEffect(() => {
    const nodeData = conversationMap[currentNode];
    if (!nodeData) return;

    const playAudio = async (audioUrl) => {
      const audio = new Audio(audioUrl);
      audio.play();
      TalkingHead.speakAudio({ audio: audioUrl });

      audio.onended = () => TalkingHead.stopLipSync();
    };

    if (nodeData.audioUrl) {
      playAudio(nodeData.audioUrl);
    } else {
      fetchGoogleTTS(nodeData.agentResponse).then((ttsAudioUrl) => {
        if (ttsAudioUrl) {
          playAudio(ttsAudioUrl);
        }
      });
    }
  }, [currentNode]);

  return null;
};

export default AudioHandler;
