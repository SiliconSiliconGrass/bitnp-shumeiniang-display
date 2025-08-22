import AbstractPlugin from "../../AbstractPlugin";
import { Application, Ticker, Color } from "pixi.js";
import { FocusController, Live2DModel, MotionPriority } from "pixi-live2d-display";

function delay(ms) {
    return new Promise(resolve => {
        setTimeout(resolve, ms);
    });
}

const modelURL = "/Resources/mikoto/mikoto.model.json";
// const modelURL = "/Resources/Mao/Mao.model3.json";

/**
 * @typedef {Object} MotionConfig
 * @property {string} group - 动作所属的分组
 * @property {number} order - 动作的排序序号
 * @property {number} duration - 动作持续时间（毫秒）
 */

/**
 * @typedef {Object.<string, MotionConfig>} MotionDictionary
 * 动作名称到动作配置的映射字典
 */

/**
 * @typedef {Object} ExpressionConfig
 * @property {number} order - 表情的排序序号
 */

/**
 * @typedef {Object.<string, ExpressionConfig>} ExpressionDictionary
 * 表情名称到表情配置的映射字典
 */

const MISAKA_MOTIONS = {
    'akimbo': {group: 'tap', order: 0, duration: 1000},
    'raise_one_hand': {group: 'tap', order: 1, duration: 1000}
}

const MISAKA_EXPRESSIONS = {
    'no_expression': {order: 0},
    'smile': {order: 1},
    'frown': {order: 2},
    'doubtful': {order: 3},
    'smile_with_eyes_closed': {order: 4},
    'shocked': {order: 5},
    'blush': {order: 6},
};

/**
 * Live2D 展示插件
 * 提供 launchMotion(motionName) 和 setExpression(expressionName) 两个方法
 */
export default class L2dDisplay extends AbstractPlugin {
    /**
     * @param {string} modelURL Live2D模型路径
     * @param {HTMLCanvasElement} canvas 画布元素
     * @param {MotionDictionary} motionDict 描述所有支持的动作名称，及其在 Live2D 所有动作中的顺序
     * @param {ExpressionDictionary} expressionDict 描述所有支持的表情名称，及其在 Live2D 所有表情中的顺序
     */
    constructor({modelURL, canvas, motionDict, expressionDict}) {
        super();
        this.modelURL = modelURL;
        this.canvas = canvas;
        this.motionDict = motionDict;
        this.expressionDict = expressionDict;
    }

    async setup(agent) {
        this.parent = agent;

        if (!agent.actionQueue) {
            throw new Error('ActionQueue not found! L2dDisplay plugin is based on ActionQueue. Load ActionQueue in advance!')
        }

        // Live2D Model and PIXI App Setup
        Live2DModel.registerTicker(Ticker);
        const app = new Application({
            resizeTo: this.canvas,
            view: this.canvas
        });
        console.log("app1", app); // debug
        // app.view.setAttribute("id", "main-canvas");
        // document.body.appendChild(app.view);
        app.renderer.backgroundAlpha = 0;

        const model = await Live2DModel.from(this.modelURL);

        this.model = model;

        model.initHeight = model.height;
        model.initWidth = model.width;

        const scale = app.view.height / model.height * 2;
        // model.anchor.set(0.5, 0.5);
        model.anchor.set(0.5, 0.6);
        model.scale.set(scale, scale);
        model.x = app.view.width / 2;
        model.y = app.view.height / 2;

        console.log('init scale', app.view.clientWidth, model.height, scale);

        app.stage.addChild(model); // add model to stage

        let focusController = new FocusController(); // mouse focus is banned
        focusController.focus = () => {};
        focusController.update = () => {};
        model.internalModel.focusController = focusController;

        // 响应窗口尺寸变化
        window.addEventListener('resize', () => {
            // resize canvas
            app.renderer.resize(app.view.clientWidth, app.view.clientHeight);

            // reset position and scale of model
            const scale = app.view.clientHeight / model.initHeight * 2;

            model.scale.set(scale, scale);

            // model.anchor.set(0.5, 0.5);
            model.anchor.set(0.5, 0.6);
            model.x = app.view.width / 2;
            model.y = app.view.height / 2;
        });

        // lip sync
        // 口型同步
        function lipSyncLoop() {
            // let ele = document.getElementById('lipSyncVal');
            
            if (agent.resourceManager) {
                let value = Number(agent.resourceManager.audioBank.volume);
                try {
                    // Cubism 2: coreModel.setParamFloat
                    model.internalModel.coreModel.setParamFloat("PARAM_MOUTH_OPEN_Y", value);
                } catch(e) {
                    // model.internalModel.coreModel.setParameterValueById('ParamMouthUp', 1);
                    model.internalModel.coreModel.setParameterValueById('ParamA', value, 1.0);
                    model.internalModel.coreModel.setParameterValueById('ParamMouthOpenY', value);
                }
            }

            // app.view.width = app.view.offsetWidth;
            // app.view.height = app.view.offsetHeight;

            requestAnimationFrame(lipSyncLoop);
        }
        lipSyncLoop();

        // 注册ActionQueue动作类型
        agent.actionQueue.registerActionType('Expression/Motion', async (action, actionQueue) => {
            if (action.type !== 'Expression/Motion') return;
            let name = action.data;
            if (name in this.motionDict) {
                this.launchMotion(name);

                const coreModel = model.internalModel.coreModel;

                const RESTORE_DELAY_DICT = {
                    '流汗': 4000,
                    '摇头': 6800,
                    '招手': 4000,
                    '指': 4000
                };

                const delaySeconds = RESTORE_DELAY_DICT[name];

                setTimeout(() => {
                    // restore model state
                    // only for shumeiniang (Fuck DAver Live2D maker!)
                    
                    coreModel.setParameterValueById("Param14", 0); // Hand Pointing
                    coreModel.setParameterValueById("ParamSweat", 0); // Sweat

                    // 最好做一下平滑化。不过根本问题在于Live2D模型的动作没有实现参数复位
                    coreModel.setParameterValueById("ParamAngleX", 0);
                    coreModel.setParameterValueById("ParamAngleY", 0);
                    coreModel.setParameterValueById("ParamAngleZ", 0);
                }, delaySeconds);

                await delay(this.motionDict[name].duration);

                

            } else if (name in this.expressionDict) {
                this.setExpression(name);
            }
        });

        console.log('L2dDisplay', this, this.model); // debug
    }

    async queryToLLM(agent, userInput) {
        return '';
    }

    /**
     * 开始 Live2D 动作
     * @param {string} motionName 动作名称
     */
    launchMotion(motionName) {
        if (motionName in this.motionDict) {
            // this.model.motion('tap', this.motionDict[motionName].order, MotionPriority.FORCE);
            this.model.motion(this.motionDict[motionName].group, this.motionDict[motionName].order, MotionPriority.FORCE);
        }
    }

    /**
     * 设置 Live2D 表情
     * @param {string} expressionName 表情名称
     */
    setExpression(expressionName) {
        if (expressionName in this.expressionDict) {
            this.model.expression(this.expressionDict[expressionName].order);
        }
    }
}
