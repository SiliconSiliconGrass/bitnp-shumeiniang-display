import { Resource } from '../plugins/silicon-plugins/ActionQueue/ResourceManager.js';
import { GetBotFromConfig } from '../Bot/BotUtils.js';
import AbstractAgent from './AbstractAgent.js';

function multipleSplit(inputString, delimiters) {
    let result = [];
    let curr = '';
    for (let i in inputString) {
        let char = inputString[i];
        curr += char;
        if (delimiters.includes(char)) {
            result.push(curr);
            curr = '';
        }
    }

    // if (curr !== '') {
    //     result.push(curr);
    // }

    result.push(curr);

    // console.log('multipleSplit', {inputString, delimiters, result});

    return result;
}
console.log(multipleSplit)

function isEmpty(str) {
    const bannedChars = "「」，。？/：；‘“’”【】、｜,.:;./'\"'=+-_)(*&^%$#@!`` \n"
    for (let char of bannedChars) str = str.replaceAll(char, '');
    return str === '';
}

function areBracketsBalanced(str) {
    const openBracketCount = (str.match(/\[/g) || []).length;
    const closeBracketCount = (str.match(/\]/g) || []).length;
    
    return openBracketCount === closeBracketCount;
}

const MIN_SENTENCE_LENGTH = 8;

const msgDelta = (self, event) => {
    // 定义收到流式请求中的message delta时的处理过程
    if (event.detail.content) {
        const delta = event.detail.content.replaceAll('（', '[').replaceAll('）', ']').replaceAll('【', '[').replaceAll('】', ']');
        self.response += delta;
        self.buffer += delta;
    }

    if (!areBracketsBalanced(self.buffer)) return; // 若不匹配，则暂不处理

    const seps = "。？！；.?!;\n、";
    // const seps = "。？！；.?!;\n";
    let splitList = self.buffer.split('[');

    if (splitList.length === 1 && multipleSplit(self.buffer, seps).length === 1) {
        return;
    }

    function addSentence(text) {

        console.log('addSentence', {text});

        let ttsResource = new Resource(self.uuid(), 'TTS', {text: text});
        let translationResource = new Resource(self.uuid(), 'Translation', {text: text, context: self.response});
        self.resourceManager.add(ttsResource); // 注册所需TTS audio 资源
        self.resourceManager.add(translationResource); // 注册所需翻译文本资源
        self.actionQueue.enqueue({type: "SayAloud", data: text, resources: [ttsResource, translationResource]}); // 将SayAloud动作加入队列
    }

    for (let i = 0; i < splitList.length; i++) {
        let chunk = splitList[i];
        if (i === 0) {
            // 第一个chunk需要特殊化处理，因为不包含"]", 直接SayAloud
            let sentences = multipleSplit(chunk, seps);
            let sentenceBuffer = '';
            for (let sentence of sentences.slice(0, -1)) {
                sentenceBuffer += sentence;
                if (sentenceBuffer.length < MIN_SENTENCE_LENGTH) continue;
                addSentence(sentenceBuffer);
                sentenceBuffer = '';
            }
            self.buffer = sentenceBuffer + (sentences[sentences.length - 1] || '');
            console.log('self.buffer =', self.buffer);
        } else if (i < splitList.length - 1) {
            // 一般的chunk处理：先按照"]"切分后，再分别处理
            let splitList_ = chunk.split(']');
            if (splitList_.length === 2) {

                // 处理方括号中的tag
                let tag = splitList_[0];
                if (tag.startsWith('zh:')) {
                    // Chinese Translation
                    self.actionQueue.enqueue({type: "Translation", data: tag.slice(3), resources: []}); // Translation动作入队
                } else {
                    // Expression/Motion
                    self.actionQueue.enqueue({type: "Expression/Motion", data: tag, resources: []}); // Expression/Motion动作入队
                }

                // 处理"]"后面的text
                let text = splitList_[1];
                let sentences = multipleSplit(text, seps);
                let sentenceBuffer = '';
                for (let sentence of sentences) {
                    sentenceBuffer += sentence;
                    if (sentenceBuffer.length < MIN_SENTENCE_LENGTH) continue;
                    addSentence(sentenceBuffer);
                    sentenceBuffer = '';
                }
                self.buffer = sentenceBuffer;
                console.log('self.buffer =', self.buffer);

            } else {
                console.warn(`Found unbalanced brackets when parsing message delta! (Current buffer: ${self.buffer})`);
            }
        } else {
            let splitList_ = chunk.split(']');
            if (splitList_.length === 2) {
                // 处理方括号中的tag
                let tag = splitList_[0];
                if (tag.startsWith('zh:')) {
                    // Chinese Translation
                    self.actionQueue.enqueue({type: "Translation", data: tag.slice(3), resources: []}); // Translation动作入队
                } else {
                    // Expression/Motion
                    self.actionQueue.enqueue({type: "Expression/Motion", data: tag, resources: []}); // Expression/Motion动作入队
                }

                // 处理"]"后面的text
                let text = splitList_[1];
                let sentences = multipleSplit(text, seps);
                let sentenceBuffer = '';
                for (let sentence of sentences.slice(0, -1)) {
                    sentenceBuffer += sentence;
                    if (sentenceBuffer.length < MIN_SENTENCE_LENGTH) continue;
                    addSentence(sentenceBuffer);
                    sentenceBuffer = '';
                }
                self.buffer = sentenceBuffer + (sentences[sentences.length - 1] || '');
                console.log('self.buffer =', self.buffer);

            } else {
                console.warn(`Found unbalanced brackets when parsing message delta! (Current buffer: ${self.buffer})`);
            }
        }
    }
    // self.buffer = '';
};

const responseDone = (self) => {

    // console.log('DEBUG 1 VTuberAgent responseDone:', self.response);
    self.bot.messages.push({
        role: "assistant",
        content: self.response,
        content_type: "text"
    });

    console.log('DEBUG 1 self.buffer =', self.buffer)
    // msgDelta(self, new CustomEvent('message_delta', {detail: {content: '\n'}}));

    self.actionQueue.enqueue({type: "EndOfResponse", data: {}, resources: []}); // 将EndOfResponse动作加入队列
    self.response = ''; // ?
    self.buffer = '';
}

/**
 * A common chat bot model
 */
export default class Agent extends AbstractAgent {
    /**
     * 
     * @param {Object} botConfig configuration for agent brain
     * @param {string | null} queryTemplate template of query prompt
     */
    constructor(botConfig, queryTemplate = null) {
        super();

        this.busy = false;

        this.bot = GetBotFromConfig(botConfig);

        this.subtitles = {'main': null, 'translation': null}; // 字幕DOM元素

        this.uuidFacotry = 0;

        this.bot.setup(); // 初始化时自动创建ConvID, 以提高首句TTS生成速度
        this.bot.addEventListener('message_delta', (event) => {
            msgDelta(this, event);
        });
        this.bot.addEventListener('done', () => {
            responseDone(this);
        });

        if (!queryTemplate) {
            queryTemplate = '[时间: %TIME%]\n%PLUGIN_INFO%\n用户的输入: %USER_INPUT%';
            // queryTemplate = '%USER_INPUT%';
        }
        this.queryTemplate = queryTemplate;

        this.buffer = '';          // 保存 message delta 以等待分句处理的缓冲区
        this.response = '';        // 用于存储一次的回答
        this.userInputBuffer = []; // 用户输入的缓冲区
        this.timeoutId = null;     // mainLoop timeout id

        this.plugins = [];         // 所有插件或扩展

        this.dispatchEvent(new CustomEvent('init')); // init
    }

    uuid() {
        return this.uuidFacotry++;
    }

    async respondToContext(messages) {
        // if (this.busy) {
        //     console.warn('VTuberAgent: I\'m busy!');
        //     return;
        // }
        this.bot.response = '';
        this.bot.buffer = '';
        this.response = '';
        this.buffer = '';
        this.busy = true;
        try {
            return await this.bot.respondToContext(messages);
        } catch (e) {
            console.warn('VTuberAgent: An error occurred when sending request to LLM bot.', e);
            this.busy = false;
        }
    }

    appendContext(text, role = 'user') {
        return this.bot.appendContext(text, role);
    }

    waitUntilEndOfResponse() {
        // 等待直到动作列表被清空
        return new Promise(resolve => {
            if (!this.actionQueue) {
                console.warn('VTuberAgent.waitUntilEndOfResponse: actionQueue plugin is not loaded!');
                resolve();
            }
            if (this.actionQueue.isEmpty()) {
                return resolve();
            }
            this.actionQueue.addEventListener('empty', resolve, { once: true });
        });
    }

    async mainLoop(self) {
        /**
         * 主循环 (向LLM进行轮询)
         */

        // console.log({this: self});

        let message = ''; // 从userInputBuffer中获取用户的全部输入

        if (self.userInputBuffer.length > 0) {
            console.log({userInputBuffer: self.userInputBuffer});
        }

        for (let userInput of self.userInputBuffer) {
            message += userInput + '\n';
        }
        self.userInputBuffer = []; // 清空userInputBffer

        let messageEmpty = (message === "");

        if (messageEmpty) {

            /* TODO: 用户没有输入的时候，应该如何表现？ */

            // if (Math.random() < 0.9) {
            //     return setTimeout(self.mainLoop, 3000);
            // }
            // message = "[系统提示: 用户什么也没输入, 如果你认为没有必须要说的话, 那就回复“。”, 如果你有想说的话或想做的动作，那就直接正常回答, 但不要一直问用户为什么不说话]";
            return setTimeout(() => self.mainLoop(self), 10);
        }

        self.dispatchEvent(new CustomEvent('start_of_response', {detail: {userInputBuffer: self.userInputBuffer}}));

        let pluginInfo = '';
        for (let plugin of self.plugins) {
            try {
                pluginInfo += await plugin.queryToLLM(self, message);
            } catch(e) {
                console.warn('An error occurred when running a plugin', {plugin: plugin, error: e});
            }
        }

        console.log({pluginInfo});

        let content = self.queryTemplate;
        content = content.replaceAll('%TIME%', `${new Date(Date.now())}`);
        content = content.replaceAll('%PLUGIN_INFO%', pluginInfo);
        content = content.replaceAll('%USER_INPUT%', message);

        self.appendContext(content, 'user');
        console.log(self.bot.messages);
        console.log('responding...');
        let response = await self.respondToContext();
        console.log({response});
        console.log('respond end');

        self.dispatchEvent(new CustomEvent('end_of_query', {detail: {
            userInputBuffer: self.userInputBuffer,
            response: response
        }})); // End Of Query

        // await self.waitUntilEndOfResponse();
        self.waitUntilEndOfResponse().then(() => {
            self.busy = false;
            self.dispatchEvent(new CustomEvent('end_of_response', {detail: {
                userInputBuffer: self.userInputBuffer,
                response: response
            }})); // End Of Response
            console.log('end of response');
        });

        let sleepTime = (self.userInputBuffer.length === 0) ? 1000 : 1000;
        self.timeoutId = setTimeout(() => self.mainLoop(self), sleepTime);
    }
}