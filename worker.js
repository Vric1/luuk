// Cloudflare Worker для Telegram РП Бота с ИИ
export default {
  async fetch(request, env, ctx) {
    // Конфигурация
    const TELEGRAM_BOT_TOKEN = env.TELEGRAM_BOT_TOKEN;
    const OPENROUTER_API_KEY = env.OPENROUTER_API_KEY;
    const MODEL_NAME = env.MODEL_NAME || "tngtech/deepseek-r1t2-chimera:free";
    
    if (!TELEGRAM_BOT_TOKEN || !OPENROUTER_API_KEY) {
      return new Response("Токены не настроены", { status: 500 });
    }

    if (request.method === "POST") {
      const update = await request.json();
      await handleUpdate(update, env);
      return new Response("OK");
    }

    return new Response("Telegram РП Бот работает!", { status: 200 });
  }
};

// РП действия
const RP_ACTIONS = {
  'hug': '🤗 обнял(а)',
  'kiss': '💋 поцеловал(а)',
  'pat': '👋 погладил(а)',
  'slap': '👋 ударил(а)',
  'poke': '👉 ткнул(а)',
  'bite': '😬 укусил(а)',
  'punch': '👊 ударил(а)',
  'kill': '💀 убил(а)',
  'feed': '🍕 накормил(а)',
  'cuddle': '🤗 обнял(а) крепко',
  'cry': '😢 плачет рядом с',
  'smile': '😊 улыбается',
  'dance': '💃 танцует с',
  'wave': '👋 машет рукой'
};

// Обработка обновлений от Telegram
async function handleUpdate(update, env) {
  if (!update.message) return;

  const message = update.message;
  const chatId = message.chat.id;
  const text = message.text;
  const user = message.from;

  if (!text) return;

  // Обработка команд
  if (text.startsWith('/start')) {
    await sendMessage(chatId, getStartMessage(user), env);
  } else if (text.startsWith('/help')) {
    await sendMessage(chatId, getHelpMessage(), env);
  } else if (text.startsWith('/profile')) {
    await sendMessage(chatId, `👤 Профиль ${user.first_name}\n\nВ Cloudflare Workers профили временно недоступны`, env);
  } else if (text.startsWith('/rp')) {
    await sendMessage(chatId, getRpCommandsList(), env);
  } else if (text.startsWith('/ai ')) {
    const prompt = text.substring(4);
    await handleAiChat(chatId, prompt, user, env);
  } else if (Object.keys(RP_ACTIONS).some(cmd => text.startsWith(`/${cmd}`))) {
    await handleRpAction(message, env);
  } else if (!text.startsWith('/')) {
    // Обычное сообщение - отвечаем через ИИ
    await handleAiChat(chatId, text, user, env);
  }
}

// Стартовое сообщение
function getStartMessage(user) {
  return `👋 Привет, ${user.first_name}!

Я РП бот с ИИ для ролевых игр в Telegram!

📝 Доступные команды:
/profile - Твой профиль  
/rp - Список РП команд
/ai - Чат с ИИ (ролевая игра)
/help - Помощь

🎭 РП команды:
/hug @username - обнять пользователя
/kiss - поцеловать (ответом на сообщение)

🤖 ИИ возможности:
• Просто напиши мне - я отвечу как ролевой персонаж!
• Работаю на Cloudflare Workers!`;
}

// Помощь
function getHelpMessage() {
  return `📆 Помощь по боту

🎭 РП команды:
Используй /rp чтобы увидеть все команды

🤖 ИИ чат:
/ai сообщение - чат с ИИ
Или просто напиши мне сообщение!

👤 Профиль:
/profile - посмотреть свой профиль

💡 Примеры:
/hug @username
/kiss (ответом на сообщение)
/ai Привет! Как дела?

⚡ Работает на Cloudflare Workers!`;
}

// Список РП команд
function getRpCommandsList() {
  let text = "🎭 Доступные РП команды:\n\n";
  for (const [cmd, action] of Object.entries(RP_ACTIONS)) {
    text += `/${cmd} - ${action}\n`;
  }
  text += "\n💡 Используй команды с @username или ответом на сообщение";
  return text;
}

// Обработка РП действий
async function handleRpAction(message, env) {
  const text = message.text;
  const user = message.from;
  const chatId = message.chat.id;
  
  // Определяем команду
  const command = text.split(' ')[0].substring(1);
  const action = RP_ACTIONS[command];
  
  if (!action) return;

  // Определяем цель
  let targetName = null;
  
  // Проверяем ответ на сообщение
  if (message.reply_to_message) {
    targetName = message.reply_to_message.from.first_name;
  } else {
    // Проверяем упоминание в тексте
    const parts = text.split(' ');
    if (parts.length > 1) {
      targetName = parts.slice(1).join(' ');
    }
  }

  if (!targetName) {
    await sendMessage(chatId, "❌ Укажи пользователя через @username или ответь на его сообщение!", env);
    return;
  }

  const rpText = `🎭 ${user.first_name} ${action} ${targetName}!`;
  await sendMessage(chatId, rpText, env);
}

// Обработка ИИ чата
async function handleAiChat(chatId, prompt, user, env) {
  try {
    // Отправляем индикатор печатания
    await sendChatAction(chatId, "typing", env);
    
    const systemPrompt = `Ты - ролевой персонаж в Telegram-чате. Твоя задача:

1. Отвечай в стиле ролевой игры
2. Будь дружелюбным и интересным собеседником  
3. Можешь использовать эмодзи
4. Ответы должны быть короткими и интересными
5. Поддерживай атмосферу ролевой игры

Пользователь: ${user.first_name}`;

    const response = await callOpenRouter(prompt, systemPrompt, env);
    await sendMessage(chatId, `🤖 ${response}`, env);
  } catch (error) {
    await sendMessage(chatId, "😔 Ошибка ИИ, попробуй чуть позже...", env);
  }
}

// Вызов OpenRouter API
async function callOpenRouter(prompt, systemPrompt, env) {
  const response = await fetch("https://openrouter.ai/api/v1/chat/completions", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${env.OPENROUTER_API_KEY}`,
      "Content-Type": "application/json",
      "HTTP-Referer": "https://t.me/your_rp_bot",
      "X-Title": "Telegram RP Bot"
    },
    body: JSON.stringify({
      model: env.MODEL_NAME || "tngtech/deepseek-r1t2-chimera:free",
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: prompt }
      ],
      max_tokens: 1000,
      temperature: 0.8
    })
  });

  if (!response.ok) {
    throw new Error(`OpenRouter API error: ${response.status}`);
  }

  const data = await response.json();
  return data.choices[0].message.content;
}

// Отправка сообщения
async function sendMessage(chatId, text, env) {
  const response = await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      chat_id: chatId,
      text: text
    })
  });

  return response.json();
}

// Отправка индикатора действия
async function sendChatAction(chatId, action, env) {
  await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendChatAction`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      chat_id: chatId,
      action: action
    })
  });
}