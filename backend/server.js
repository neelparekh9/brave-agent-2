require('dotenv').config();
const express = require('express');
const cors = require('cors');
const OpenAI = require('openai');
const script = require('./Script.js');

const app = express();
app.use(cors());
app.use(express.json());

const PORT = process.env.PORT || 3001;

let openai;
try {
    openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
} catch (e) {
    console.warn("OpenAI API key not provided. TTS will fail unless configured.");
}

app.post('/api/next-turn', async (req, res) => {
    const { nodeId, agentType } = req.body;
    if (!nodeId) {
        return res.status(400).json({ error: 'nodeId is required' });
    }

    const nodeData = script[nodeId];
    if (!nodeData) {
        return res.status(404).json({ error: `Node ${nodeId} not found` });
    }

    const textToSpeak = nodeData.agentResponse || "";
    let audioBase64 = null;

    if (textToSpeak && openai) {
        const selectedVoice = agentType === 'female' ? 'nova' : 'onyx';
        try {
            const mp3 = await openai.audio.speech.create({
                model: "tts-1",
                voice: selectedVoice,
                input: textToSpeak,
            });
            const buffer = Buffer.from(await mp3.arrayBuffer());
            audioBase64 = buffer.toString('base64');
        } catch (error) {
            console.error("OpenAI TTS Error:", error);
        }
    }

    res.json({
        nodeId,
        agentResponse: textToSpeak,
        nextOptions: nodeData.nextOptions || [],
        animation: nodeData.animation || ["Idle"],
        audioBase64
    });
});

app.listen(PORT, () => {
    console.log(`Scripted Audio Backend listening on port ${PORT}`);
});
