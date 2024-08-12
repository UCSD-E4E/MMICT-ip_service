import torch
import torch.nn.functional as F
import torch.nn.init as init
import torch.nn as nn
from torch.nn import ConvTranspose2d, Conv2d, Module
from torchgeo.models import resnet18, resnet50, get_weight
from torchvision.models.resnet import ResNet
from typing import Optional
from satlaspretrain_models import Head, Weights
weights_manager = Weights()

"""
Pretrained model Weights from SSL4EO-12 dataset
@ https://github.com/zhu-xlab/SSL4EO-S12

Imported using torchgeo
@ https://torchgeo.readthedocs.io/en/stable/api/models.html

SWIN high resolution aerial imagery model from Satlas
@ https://github.com/allenai/satlas

New weights can be imported from torchgeo using:
torchgeo.models.get_weight("ResNet50_Weights.SENTINEL2_ALL_MOCO")
"""

"""
   _____   _                       _    __   _                     
  / ____| | |                     (_)  / _| (_)                    
 | |      | |   __ _   ___   ___   _  | |_   _    ___   _ __   ___ 
 | |      | |  / _` | / __| / __| | | |  _| | |  / _ \ | '__| / __|
 | |____  | | | (_| | \__ \ \__ \ | | | |   | | |  __/ | |    \__ \
  \_____| |_|  \__,_| |___/ |___/ |_| |_|   |_|  \___| |_|    |___/
                                                                   
"""                                                             

class ResNet50_UNet(Module):
    """
    UNet architecture with ResNet50 encoder. 
    
    Default ResNet is trained on Sentinel-2 3 channel RGB satellite imagery.
    ResNet50 models trained on other inputs can be used.
    
    """
    def __init__(self, ResNet50 : Optional[ResNet] = None, num_channels=3, input_image_size=256):
        super().__init__()
        self.num_channels = num_channels
        
        if ResNet50 == None:
            ResNet50=resnet50(
                weights=get_weight("ResNet50_Weights.SENTINEL2_RGB_SECO")
            )

        # Pretrained Encoder with frozen weights
        self.layer1 = nn.Sequential(
            ResNet50.conv1,
            ResNet50.bn1,
            nn.ReLU(),
            ResNet50.maxpool,
            ResNet50.layer1,
        )
        self.layer1.requires_grad_(False)
        self.layer2 = ResNet50.layer2
        self.layer2.requires_grad_(False)
        self.layer3 = ResNet50.layer3
        self.layer3.requires_grad_(False)
        self.layer4 = ResNet50.layer4
        self.layer4.requires_grad_(False)

        # Center
        self.center = Upsample(2048, 1536, 1024)

        # Skip connections
        self.skip_conv1 = Conv2d(1024, 1024, kernel_size=1)
        self.skip_conv2 = Conv2d(512, 512, kernel_size=1)
        self.skip_conv3 = Conv2d(256, 256, kernel_size=1)

        # Decoder
        self.decoder1 = Upsample(1024+1024, 1024, 512)
        self.decoder2 = Upsample(512+512, 512, 256)
        self.decoder3 = Upsample(256+256, 256, 128)
        self.classification_head = nn.Sequential(
          Upsample(128, 128, 64),
          Conv2d(64, 1, kernel_size=1),
          nn.Upsample(
              size=(input_image_size, input_image_size),
              mode="bilinear",
              align_corners=False,
          )
        )
    
    def forward(self, image):
        image = image[:, :self.num_channels, :, :]
        
        # Encode
        x1 = self.layer1(image)  # 256
        x2 = self.layer2(x1)  # 512
        x3 = self.layer3(x2)  # 1024
        x4 = self.layer4(x3)  # 2048

        # Center
        x = self.center(x4)
        
        # decode
        x = torch.cat((x, self.skip_conv1(x3)), dim=1)
        x = self.decoder1(x)
        x = torch.cat((x, self.skip_conv2(x2)), dim=1)
        x = self.decoder2(x)
        x = torch.cat((x, self.skip_conv3(x1)), dim=1)
        x = self.decoder3(x)
        x = self.classification_head(x)

        return x

class ResNet18_UNet(Module):
    """
    UNet architecture with ResNet18 encoder.
    
    Default ResNet is trained on Sentinel-2 3 channel RGB satellite imagery.
    """
    def __init__(self, ResNet18 : Optional[ResNet] = None, input_image_size=128):
        super(ResNet18_UNet, self).__init__()
        if ResNet18 is None:
            ResNet18 = resnet18(
                weights=get_weight("ResNet18_Weights.SENTINEL2_RGB_SECO")
            )
        
        # Pretrained Encoder with frozen weights
        self.layer1 = nn.Sequential(
            ResNet18.conv1,
            ResNet18.bn1,
            nn.ReLU(),
            ResNet18.maxpool,
            ResNet18.layer1,
        )
        self.layer1.requires_grad_(False)
        self.layer2 = ResNet18.layer2
        self.layer2.requires_grad_(False)
        self.layer3 = ResNet18.layer3
        self.layer3.requires_grad_(False)
        self.layer4 = ResNet18.layer4
        self.layer4.requires_grad_(False)

        # Center
        self.center = Upsample(512, 312, 256)

        # Skip connections
        self.skip_conv1 = Conv2d(256, 256, kernel_size=1)
        self.skip_conv2 = Conv2d(128, 128, kernel_size=1)
        self.skip_conv3 = Conv2d(64, 64, kernel_size=1)

        #decoder
        self.decoder1 = Upsample(256+256, 256, 128)
        self.decoder2 = Upsample(128+128, 128, 64)
        self.decoder3 = Upsample(64+64, 64, 32)
        
        self.classification_head = nn.Sequential(
            Conv2d(32, 1, kernel_size=2, padding=1),
            nn.Upsample(
              size=(input_image_size, input_image_size),
              mode="bilinear",
              align_corners=False,
            )
        )

    def forward(self, image):
        image = image[:, :3, :, :]

        # Encode
        x1 = self.layer1(image)  # 64
        x2 = self.layer2(x1)  # 128
        x3 = self.layer3(x2)  # 256
        x4 = self.layer4(x3)  # 512
      
        # Center
        x = self.center(x4)

        # Decode
        x = torch.cat((x, self.skip_conv1(x3)), dim=1)
        x = self.decoder1(x)
        x = torch.cat((x, self.skip_conv2(x2)), dim=1)
        x = self.decoder2(x)
        x = torch.cat((x, self.skip_conv3(x1)), dim=1)
        x = self.decoder3(x)
        x = self.classification_head(x)
        
        return x
    
class SwinB_UNet(Module):
    """
    Encoder: Swin Transformer pretrained on Satlas 0.5-2 m/pixel aerial images
    Decoder: U-net with CE loss
    
    Expected input is 8-bit (0-255) aerial images at 0.5 - 2 m/pixel.
    The 0-255 pixel values should be divided by 255 so they are 0-1.
    example_input = torch.rand((1, 3, 512, 512), dtype=torch.float32)
    """
    def __init__(self):
        super().__init__()

        # Load the pretrained model to cpu
        self.model = weights_manager.get_pretrained_model(
            "Aerial_SwinB_SI", fpn=True, head=Head.SEGMENT, num_categories=1, device='cpu'
        )
        for _, param in self.model.backbone.named_parameters():
            param.requires_grad = False  # Freeze backbone parameters
        self.filter = ProcessSwinPrediction()

    def forward(self, image):
        x = self.model(image)
        x = self.filter(x)
        return x


"""
  _____    _    __    __                 _                 
 |  __ \  (_)  / _|  / _|               (_)                
 | |  | |  _  | |_  | |_   _   _   ___   _    ___    _ __  
 | |  | | | | |  _| |  _| | | | | / __| | |  / _ \  | '_ \ 
 | |__| | | | | |   | |   | |_| | \__ \ | | | (_) | | | | |
 |_____/  |_| |_|   |_|    \__,_| |___/ |_|  \___/  |_| |_|
                                                                                                                  
"""
class MangroveDiffusion(Module):
    def __init__(self, decoder : Module, encoder : Module,
                  feature_size: int = 2048, diffusion_weights = None):
        super().__init__()
        
        self.encoder = encoder
        self.encoder.requires_grad_(False)

        self.adaptive_pool = torch.nn.AdaptiveMaxPool2d((9,9))
        
        self.decoder = decoder
        self.decoder.requires_grad_(False)
        
        self.reverse_diffuser = torch.nn.Linear(feature_size + feature_size + 1, feature_size)
    
    def forward(self, image):
        x = self.encoder(image)
        x = self.adaptive_pool(x)
        x = self.decoder(x)
        return x

"""
  _    _          _                             
 | |  | |        | |                            
 | |__| |   ___  | |  _ __     ___   _ __   ___ 
 |  __  |  / _ \ | | | '_ \   / _ \ | '__| / __|
 | |  | | |  __/ | | | |_) | |  __/ | |    \__ \
 |_|  |_|  \___| |_| | .__/   \___| |_|    |___/
                     | |                        
                     |_|                        
"""
class Upsample(Module):
    """
    Helper class for the UNet architecture.
    Uses convolutional layers to upsample the input.
    """
    def __init__(self, in_channel, mid_channel, out_channel):
        super(Upsample, self).__init__()
        self.upsampler = nn.Sequential(
            Conv2d(in_channel, mid_channel, kernel_size=3, padding=1),
            nn.ReLU(),
            ConvTranspose2d(mid_channel, out_channel, kernel_size=2, stride=2)
        )
        self.initialize_weights()
    
    def forward(self, x) -> torch.Tensor:
        return self.upsampler(x)
    
    def initialize_weights(self):
        for m in self.upsampler:
            if isinstance(m, Conv2d) or isinstance(m, ConvTranspose2d):
                init.kaiming_uniform_(m.weight, nonlinearity='relu')
                if m.bias is not None:
                    init.constant_(m.bias, 0)
    
class ProcessSwinPrediction(Module):
    def __init__(self):
        super().__init__()

    def forward(self, x):
        prediction, _ = x
        # Apply the processing module to the prediction
        return prediction