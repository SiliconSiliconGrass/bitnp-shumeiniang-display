import { Application, Ticker } from "pixi.js";
import { FocusController, Live2DModel } from "pixi-live2d-display";
// import { FocusController, Live2DModel, MotionPriority } from "pixi-live2d-display";

const BACKEND_PORT = 9234; // facecap backend port

class ParamTransfer {
    /**
     * 用于将面捕参数迁移为模型参数
     * @param {string} faceParamName 面捕参数名
     * @param {string} modelParamName 模型参数名
     * @param {number} scale 缩放系数
     * @param {number} bias 偏置
     * @param {number} modelDefault 模型默认值
     */
    constructor(faceParamName, modelParamName, scale = 1, bias = 0, modelDefault = 0, active_function = undefined) {
        this.faceParamName = faceParamName;
        this.modelParamName = modelParamName;
        this.scale = scale;
        this.bias = bias;
        this.modelDefault = modelDefault;

        if (active_function == undefined) {
            active_function = x => x;
        }
        this.active_function = active_function;
    }

    transfer(faceParamValue) {
        return this.active_function(faceParamValue * this.scale + this.bias);
    }
}

const PARAM_TRANSFER_MAP = [
    new ParamTransfer("eyeBlinkLeft", "ParamEyeLOpen", -2, 1, 1),
    new ParamTransfer("eyeBlinkRight", "ParamEyeROpen", -2, 1, 1),
    new ParamTransfer("jawOpen", "ParamMouthOpenY", 4, 0, 0),
    new ParamTransfer("rotatePitch", "ParamAngleY", 1, 0, 0),
    new ParamTransfer("rotateYaw", "ParamAngleX", -1, 0, 0),
    new ParamTransfer("rotateRoll", "ParamAngleZ", 1, 0, 0),

    // new ParamTransfer("rotatePitch", "ParamBodyAngleY", 1, 0, 0),
    // new ParamTransfer("rotateYaw", "ParamBodyAngleX", -1, 0, 0),
    // new ParamTransfer("rotateRoll", "ParamBodyAngleZ", 1, 0, 0),
]

export async function live2d_setup(canvas, modelURL) {

    // Live2D Model and PIXI App Setup
    Live2DModel.registerTicker(Ticker);
    const app = new Application({
        resizeTo: canvas,
        view: canvas
    });
    // app.view.setAttribute("id", "main-canvas");
    // document.body.appendChild(app.view);
    app.renderer.backgroundAlpha = 0;

    const model = await Live2DModel.from(modelURL);

    model.initHeight = model.height;
    model.initWidth = model.width;

    const scale = app.view.height / model.height * 2;
    model.anchor.set(0.5, 0.6);
    model.scale.set(scale, scale);
    model.x = app.view.width / 2;
    model.y = app.view.height / 2;

    console.log('init scale', app.view.clientWidth, model.height, scale);

    app.stage.addChild(model); // add model to stage

    // let focusController = new FocusController(); // mouse focus is banned
    // focusController.focus = () => {};
    // focusController.update = () => {};
    
    console.log(FocusController)

    console.log(model); // debug

    let dictParams = {}; // 存储参数值的字典
    function handleModelUpdate(model, dictParams) {
        // 处理模型更新
        const coreModel = model.internalModel.coreModel;
        for (let paramName in dictParams) {
            coreModel.setParameterValueById(paramName, dictParams[paramName]);
        }
    }

    // 覆盖focus函数
    model.internalModel.focusController.old_update = model.internalModel.focusController.update
    model.internalModel.focusController.update = function (...args) {
        // model.internalModel.focusController.targetX = dictParams["ParamAngleX"] || 0;
        // model.internalModel.focusController.targetY = dictParams["ParamAngleY"] || 0;
        model.internalModel.focusController.focus(dictParams["ParamAngleX"] / 30, dictParams["ParamAngleY"] / 30)
        model.internalModel.focusController.old_update(...args)
    }

    // 覆盖模型的update函数，以实现自定义参数更新
    model.internalModel.coreModel.old_update = model.internalModel.coreModel.update;
    model.internalModel.coreModel.update = function (...args) {
        handleModelUpdate(model, dictParams);
        model.internalModel.coreModel.old_update(...args);
    }

    // 循环从服务器获取参数
    async function loopFetchParams() {
        try {
            const url = `http://127.0.0.1:${BACKEND_PORT}/get`;
            const response = await fetch(url);
            let data = await response.json();
            data = data.faceParams

            // 将面捕参数迁移为模型参数
            for (let paramTransfer of PARAM_TRANSFER_MAP) {
                if (data[paramTransfer.faceParamName] == undefined) {
                    dictParams[paramTransfer.modelParamName] = paramTransfer.modelDefault;
                } else {
                    // dictParams[paramTransfer.modelParamName] = paramTransfer.transfer(data[paramTransfer.faceParamName]);

                    // 简单的参数平滑化
                    let targetValue = paramTransfer.transfer(data[paramTransfer.faceParamName]);
                    let originalValue = dictParams[paramTransfer.modelParamName];
                    if (originalValue == undefined) {
                        originalValue = paramTransfer.modelDefault;
                    }
                    const k = 0.2
                    dictParams[paramTransfer.modelParamName] = targetValue * k + originalValue * (1 - k)
                }
            }

        } catch (error) {
            console.error('获取参数时出错:', error);
        } finally {
            setTimeout(loopFetchParams, 10);
        }
    }
    loopFetchParams();    

    // 响应窗口尺寸变化
    window.addEventListener('resize', () => {
        // resize canvas
        app.renderer.resize(app.view.clientWidth, app.view.clientHeight);

        // reset position and scale of model
        const scale = app.view.height / model.initHeight * 2;
        model.anchor.set(0.5, 0.6);
        model.scale.set(scale, scale);
        model.x = app.view.width / 2;
        model.y = app.view.height / 2;
    });
}
