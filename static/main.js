import { GoogleGenerativeAI } from "@google/generative-ai";
const conv = new showdown.Converter();

const genAI = new GoogleGenerativeAI("AIzaSyC5RpRId9Pft5kQY0_p36w8YYxkJ3g8ihI");
const gen_model = genAI.getGenerativeModel({ model: "gemini-pro" });
const chat = gen_model.startChat({
	generationConfig: {
		maxOutputTokens: 1000,
	},
});

const chatGemini = async (message) => {
	addMessage(message, "end");
	let res = await chat.sendMessage(message);
	res = await res.response;
	console.log(res);
	let html = conv.makeHtml(res.text());
	addMessage(html, "start");
}
const addMessage = (msg, direction) => {
	const messageHolder = document.getElementById("messageHolder");
	const message = document.createElement("div");
	const colour = direction !== "start" ? "gray-900" : "gray-100";
	const textcolour = direction !== "start" ? "white" : "black";
	message.innerHTML = `
	<div class="flex flex-col items-${direction}">
			<div class="bg-${colour} px-4 py-2 rounded-md text-${textcolour} w-fit 
			max-w-4xl mb-1">${msg}</div>
		</div>
	`
	messageHolder.appendChild(message);
}

const messageInput = document.getElementById("chat");
const sendBtn = document.getElementById("btn");

sendBtn.addEventListener("click", function () {
	const message = messageInput.value;
	chatGemini(message);
	messageInput.value = "";
});
