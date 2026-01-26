# 知识库 977

## 标题
万全T220/T270集成SATA RAID的配置是否可以将板载RAID功能取消？

## 问题描述
万全T220/T270集成SATA RAID的配置是否可以将板载RAID功能取消？

## 分类
主类别: 内置设备
子类别: 硬盘

## 关键词
RAID, 服务器, SATA, 硬盘

## 元信息
创建时间:2024-12-15|版本:1.0

## 解决方案
**故障描述：**

用户的[服务器](/detail/kd_17589.html)为[主板](/detail/kd_17352.html)集成2通道S[ATA](/detail/kd_17378.html) [RAID](/detail/kd_17695.html)配置（[BI](/detail/kd_17343.html)[OS](/detail/kd_17441.html)版本v1.6或v2.0），在BIOS中无法将RAID功能屏蔽，无法将[SATA](/detail/kd_17379.html)[硬盘](/detail/kd_17342.html)单独使用。

**问题分析：**

BIOS中的一些选项在出厂前被屏蔽，无法将RAID功能直接取消（选项中只有YES，没有NO），无法关闭PATA增强模式，所以用常规做法无法取消RAID。

**解决方案：**

进入BIOS主菜单，选择ADVANCED子菜单，选择[IDE](/detail/kd_17636.html) Configration,将P-ATA ONLY直接改成PATA&SATA即可。保存并重新[启动](/detail/kd_17514.html)后，就可以在这个菜单中看到两块硬盘。

<!-- 文档主题：万全T220/T270集成SATA RAID的配置是否可以将板载RAID功能取消？ (知识库库编号: 977) -->