import sys
sys.path.append("../")

import openvino.runtime as ov
from openvino.preprocess import PrePostProcessor
from openvino.preprocess import ColorFormat
from openvino.runtime import Layout, Type
import numpy as np
import cv2
from utils import Inference, get_image


"""openvino图片预处理方法
input(0)/output(0) 按照id找指定的输入输出,不指定找全部的输入输出
# input().tensor()       有7个方法
ppp.input().tensor().set_color_format().set_element_type().set_layout() \
                    .set_memory_type().set_shape().set_spatial_dynamic_shape().set_spatial_static_shape()
# output().tensor()      有2个方法
ppp.output().tensor().set_layout().set_element_type()
# input().preprocess()   有8个方法
ppp.input().preprocess().convert_color().convert_element_type().mean().scale() \
                        .convert_layout().reverse_channels().resize().custom()
# output().postprocess() 有3个方法
ppp.output().postprocess().convert_element_type().convert_layout().custom()
# input().model()  只有1个方法
ppp.input().model().set_layout()
# output().model() 只有1个方法
ppp.output().model().set_layout()
"""


class OVInference(Inference):
    def __init__(self, model_path: str, mode: str = 'CPU', **kwargs) -> None:
        """
        Args:
            model_path (str): 模型路径
            size (list[int]): 推理图片大小 [H, W]
            mode (str, optional): CPU or GPU or GPU.0  Defaults to CPU. 具体可以使用设备可以运行 samples/python/hello_query_device/hello_query_device.py 文件查看

        """
        super().__init__(**kwargs)
        # 1.载入模型
        self.model = self.get_model(model_path, mode.upper())
        # 2.保存模型输入输出
        self.inputs  = self.model.inputs
        self.outputs = self.model.outputs
        self.logger.info(f"inputs: {self.inputs}")   # inputs: [<ConstOutput: names[images] shape[1,3,640,640] type: f32>]
        self.logger.info(f"outputs: {self.outputs}") # outputs: [<ConstOutput: names[output0] shape[1,25200,85] type: f32>

        # 3.预热模型
        self.warm_up()

    def get_model(self, model_path: str, mode: str='CPU') -> ov.CompiledModel:
        """获取模型
        Args:
            model_path (str):       模路径, xml or onnx
            mode (str, optional): CPU or GPU. Defaults to CPU.
        Returns:
            CompileModel: 编译好的模型
        """
        # 这里乘以255相当于归一化和标准化同时计算
        # mean = np.array((0.485, 0.456, 0.406)) * 255
        # std  = np.array((0.229, 0.224, 0.225)) * 255
        # mean = np.array((0.485, 0.456, 0.406)) * 255
        std  = np.array((255, 255, 255))

        # Step 1. Initialize OpenVINO Runtime core
        core = ov.Core()
        # Step 2. Read a model
        model = core.read_model(model_path)

        # 使用openvino数据预处理
        if self.openvino_preprocess:
            # Step 4. Inizialize Preprocessing for the model  openvino数据预处理
            # https://mp.weixin.qq.com/s/4lkDJC95at2tK_Zd62aJxw
            # https://blog.csdn.net/sandmangu/article/details/107181289
            # https://docs.openvino.ai/latest/openvino_2_0_preprocessing.html
            ppp = PrePostProcessor(model)
            # 设定图片数据类型，形状，通道排布为RGB
            ppp.input(0).tensor().set_color_format(ColorFormat.RGB) \
                .set_element_type(Type.f32).set_layout(Layout("NCHW"))   # BGR -> RGB Type.u8 -> Type.f32  NHWC -> NCHW
            # 预处理: 改变类型,转换为RGB,减去均值,除以标准差(均值和标准差包含了归一化)
            # ppp.input(0).preprocess().convert_color(ColorFormat.RGB).convert_element_type(Type.f32).mean(mean).scale(std)
            ppp.input(0).preprocess().scale(std)
            # 指定模型输入形状
            ppp.input(0).model().set_layout(Layout("NCHW"))
            # 指定模型输出类型
            ppp.output(0).tensor().set_element_type(Type.f32)

            # Embed above steps in the graph
            model = ppp.build()

        compiled_model = core.compile_model(model, device_name=mode)
        return compiled_model

    def infer(self, image: np.ndarray) -> list[np.ndarray]:
        """推理单张图片
        Args:
            image (np.ndarray): 图片 [B, C, H, W]
        Returns:
            np.ndarray: boxes [B, 25200, 85]
        """
        # 1.推理 多种方式
        # https://docs.openvino.ai/latest/openvino_2_0_inference_pipeline.html
        # https://docs.openvino.ai/latest/notebooks/002-openvino-api-with-output.html#

        # 1.1 使用推理请求
        # infer_request = self.model.create_infer_request()
        # results       = infer_request.infer({self.inputs[0]: x})               # 直接返回推理结果
        # results       = infer_request.infer({0: x})                            # 直接返回推理结果
        # results       = infer_request.infer([x])                               # 直接返回推理结果
        # result0       = infer_request.get_output_tensor(self.outputs[0].index) # 通过方法获取单独结果  outputs[0].index 可以用0 1代替

        # 1.2 模型直接推理
        # results = self.model({self.inputs[0]: x})
        # results = self.model({0: x})
        results = self.model([image])   # return dict

        boxes = results[self.outputs[0]]

        return [boxes]


if __name__ == "__main__":
    config = {
        "model_path":           r"../weights/yolov5s_openvino_model/yolov5s.xml",
        # 使用不同精度的openvino模型不需要提前将图片转换为对应的格式,但ort和trt需要,即需要设定 `fp16=True/False` 参数
        "mode":                 r"cpu",
        "yaml_path":            r"../weights/yolov5.yaml",
        "confidence_threshold": 0.25,   # 只有得分大于置信度的预测框会被保留下来,越大越严格
        "score_threshold":      0.2,    # nms分类得分阈值,越大越严格
        "nms_threshold":        0.45,   # 非极大抑制所用到的nms_iou大小,越小越严格
        "openvino_preprocess":  True,   # 是否使用openvino图片预处理
    }

    # 实例化推理器
    inference = OVInference(**config)

    # 单张图片推理
    IMAGE_PATH = r"../images/bus.jpg"
    SAVE_PATH  = r"./ov_det.jpg"
    image_rgb = get_image(IMAGE_PATH)
    result, image_bgr_detect = inference.single(image_rgb, only_get_boxes=False)
    print(result)
    cv2.imwrite(SAVE_PATH, image_bgr_detect)

    # 多张图片推理
    IMAGE_DIR = r"../../datasets/coco128/images/train2017"
    SAVE_DIR  = r"../../datasets/coco128/images/train2017_res"
    # inference.multi(IMAGE_DIR, SAVE_DIR, save_xml=True)
    # avg transform time: 3.65625 ms, avg infer time: 43.3828125 ms, avg nms time: 0.0390625 ms, avg figure time: 0.0 ms
