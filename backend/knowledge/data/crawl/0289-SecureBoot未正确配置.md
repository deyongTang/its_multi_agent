# 知识库 289

## 标题
SecureBoot未正确配置

## 问题描述
Windows 8.1 SecureBoot未正确配置的解决方法......

## 分类
主类别: 操作系统故障
子类别: 系统应用操作

## 关键词
SecureBoot, 未正确配置, boot, 安全启动

## 元信息
创建时间:2025-09-11|版本:3.0

## 解决方案
**相关文章**:

[Windows 8.1 SecureBoot未正确配置的解决方法](https://iknow.lenovo.com.cn/detail/115519)

在BIOS中打开SecureBoot即可。

请先进入BIOS，根据具体界面，按照以下步骤操作：

**1、IdeaPad U/S/Y、Erazer Z/N、Yoga、Flex系列机型BIOS参考如下设置：**

在将"**Secure Boot**”设置为"**Enabled**”后，"**Secure Boot Status**”如果依然为关闭状态，如下图所示：

![](https://chinakb.lenovo.com.cn/_eWebEditor/uploadfile/20140526153830001.jpg)

**请执行以下步骤：**  
  
**步骤1：**在机器重启至"**Lenovo字样的屏幕**”时，不停敲击"**F2**”键或"**Fn+F2**”键进入BIOS。选择"**Security**”选项，选择"**Reset to Setup Mode**”并敲回车，选择"**YES**”并按下"**回车**”键。

**步骤2：**选择"**Restore Factory Keys**”并敲回车，选择"**YES**”并按下"**回车**”键。

**步骤3：**按"**F9**”或"**FN+F9**”恢复BIOS默认设置。

**步骤4：**按"**F10**”或"**FN+F10**”保存退出，并不停敲击"**F2**”键或"**Fn+F2**”键进入BIOS。检查"**Secure Boot Status**”此时应已经变为**Enabled**”状态，保存退出即可。

**步骤5：**进入系统后就会发现桌面右下角显示的"**SecureBoot未正确配置**”提示消息消失了。  
  
注：扬天VBKEM系列机型如遇到此类问题，BIOS设置方法与上述方案相同，只是BIOS界面略有区别

**2、IdeaPad G系列机型（如G480）BIOS参考如下设置：**

在"**Security**”菜单项下"**Secure Boot Status**”为关闭状态，且不可更改。

**请执行以下步骤**：

**步骤1：**在机器重启至"**Lenovo字样的屏幕**”时，不停敲击"**F2**”键或"**Fn+F2**”键进入BIOS。选择"**Boot**”菜单项，并将"**Boot Mode**”选项选择为"**UEFI”**模式。

**步骤2：**选择**"Exit”**菜单项，并将"**OS Optimized Defaults**”选项选择为"**WIN8 64bit**”模式。

**步骤3：**按"**F10**”或"**FN+F10**”保存退出，并不停敲击"**F2**”键或"**Fn+F2**”键进入BIOS。

**步骤4：**此时再检查"**Security**”菜单项下"**Secure Boot Status**”即为开启状态。

**步骤5：**进入系统后就会发现桌面右下角显示的"**SecureBoot未正确配置**”提示消息消失了。

<!-- 文档主题：SecureBoot未正确配置 (知识库库编号: 289) -->