import React, { useEffect, useRef, useState } from "react";
import { TalkingHead } from "../libs/talkinghead.js";

const VirtualAgent = ({ nodeData }) => {
  const avatarRef = useRef(null);
  const headInstance = useRef(null);
  const initialized = useRef(false);

  const agentType = localStorage.getItem("agentType") || "male";
  const avatarUrl =
    agentType === "female"
      ? "/models/female-avatar.glb"
      : "/models/original-avatar.glb";

  useEffect(() => {
    if (initialized.current) return;
    initialized.current = true;
    if (headInstance.current) return;

    const initializeTalkingHead = async () => {
      try {
        if (!avatarRef.current) {
          console.error("❌ Avatar container not found.");
          return;
        }

        console.log("🚀 Initializing TalkingHead...");
        const head = new TalkingHead(avatarRef.current, {
          ttsEndpoint: "https://eu-texttospeech.googleapis.com/v1beta1/text:synthesize",
          ttsApikey: process.env.REACT_APP_GOOGLE_TTS_API_KEY,
          lipsyncModules: ["en"],
          cameraView: "mid",
          cameraDistance: 1.2,
          cameraX: 0,
          cameraY: -0.2,
          avatarMood: "neutral",
        });

        await head.showAvatar(
          {
            url: avatarUrl,
            body: agentType === "female" ? "F" : "M",
            avatarMood: "happy",
            lipsyncLang: "en",
          },
          (ev) => {
            if (ev.lengthComputable) {
              console.log(`📦 Avatar Loading: ${Math.round((ev.loaded / ev.total) * 100)}%`);
            }
          }
        );

        console.log("✅ Avatar Loaded Successfully!");
        headInstance.current = head;
      } catch (error) {
        console.error("❌ Failed to initialize TalkingHead:", error);
      }
    };

    initializeTalkingHead();
  }, [avatarUrl, agentType]);

  const handleSpeech = async (node) => {
    try {
      if (!node || !headInstance.current) return;

      if (node.animation && typeof headInstance.current.playGesture === "function") {
        console.log("🎭 Playing animation:", node.animation[0]);
        headInstance.current.playGesture(node.animation[0], 3, false, 1000);
      }

      if (node.audioBase64) {
        console.log("🗣️ Speaking with OpenAI TTS audio...");
        const audioSrc = "data:audio/mp3;base64," + node.audioBase64;
        const response = await fetch(audioSrc);
        const arrayBuffer = await response.arrayBuffer();
        const audioBuffer = await headInstance.current.audioCtx.decodeAudioData(arrayBuffer);

        headInstance.current.speakAudio({
          audio: audioBuffer,
          words: [node.agentResponse],
          wtimes: [0],
          wdurations: [audioBuffer.duration * 1000]
        });
      } else if (node.agentResponse) {
        console.log("🗣️ Speaking fallback text (no TTS buffer):", node.agentResponse);
        headInstance.current.speakText(node.agentResponse);
      }
    } catch (error) {
      console.error("❌ Error during speech handling:", error);
    }
  };

  useEffect(() => {
    if (nodeData) {
      handleSpeech(nodeData);
    }
  }, [nodeData]);

  return (
    <div className="virtual-agent">
      <div
        id="avatar"
        ref={avatarRef}
        style={{
          width: "400px",
          height: "500px",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          overflow: "hidden",
          backgroundColor: "transparent",
        }}
      />
    </div>
  );
};

export default VirtualAgent;
