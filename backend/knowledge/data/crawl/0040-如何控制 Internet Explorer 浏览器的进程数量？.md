# 知识库 40

## 标题
如何控制 Internet Explorer 浏览器的进程数量？

## 问题描述
您希望了解有关如何控制、合并、减少这些 IEXPLORE.EXE 进程，使 Windows 在运行同时打开多个选项卡的 IE 9 或 IE 8 时使用尽量少的或唯一的 IEXPLORE.EXE 进程，那么您可以参考本文提供的信息。

## 分类
主类别: 操作系统故障
子类别: 浏览器

## 关键词
控制, ie, 浏览器, 进程, 数量

## 元信息
创建时间:2024-12-15|版本:1.0

## 解决方案
当您在运行 Windows 7/Server 2008（R2）/Vista 的计算机中使用 IE 9，或者在运行 Windows 7/Server 2008（R2）/Vista、Windows XP/Server 2003（R2） 的计算机中使用 IE 8 时，如果您为 IE 浏览器同时打开了多个选项卡，您可能会在 Windows 任务管理器的“**进程**”列表中看到多个不同的 IEXPLORE.EXE 进程同时运行。在 IE 的早期版本（IE 7、IE 6）中没有此现象。

您希望了解有关如何控制、合并、减少这些 IEXPLORE.EXE 进程，使 Windows 在运行同时打开多个选项卡的 IE 9 或 IE 8 时使用尽量少的或唯一的 IEXPLORE.EXE 进程，那么您可以参考本文提供的信息。

**问题分析**

IE 浏览器在同时打开多个选项卡后，Windows 会同时运行多个不同的 IEXPLORE.EXE 进程，这个现象并非是不正常的故障，而是 IE 浏览器在 IE 8 及后续的版本中引入的“**松散耦合进程框架（Loosely Coupled IE）**”进程管理技术。此技术允许 IE 浏览器将主窗口与选项卡用不同的、分离的 IEXPLORE.EXE 进程隔开。如果一个选项卡遇到了问题需要关闭，可以避免连带影响整个 IE 浏览器主窗口及其它选项卡。这样有助于提升 IE 浏览器的稳定性与安全性。

在默认的系统设置中，IE 8 或 IE 9 在启动后将至少有两个 IEXPLORE.EXE 进程运行，一个对应 IE 浏览器的主窗口、一个对应主窗口中的选项卡（一个 IE 主窗口必须至少有一个选项卡）。随着 IE 浏览器启动更多选项卡，Windows 将会运行更多若干个分离的 IEXPLORE.EXE 进程，分别对应增加的不同选项卡。IEXPLORE.EXE 进程增加的最大数量将由您计算机的可用内存与空闲的系统资源决定。

![](https://webdoc.lenovo.com.cn/lenovowsi/20120806/1344236992544_193.png)

**问题解决**

如果您希望改变 IE 浏览器的始终使用分离的 IEXPLORE.EXE 进程的默认设置、希望在运行同时打开多个选项卡的 IE 浏览器时使用尽量少的或唯一的 IEXPLORE.EXE 进程，您可以通过自行设置注册表项 TabProcGrowth 的方法实现。

警告：注册表编辑器使用不当可导致严重问题，可能需要重新安装操作系统。Microsoft 不能保证您可以解决因为注册表编辑器使用不当而导致的问题。使用注册表编辑器需要您自担风险。

修改注册表之前，一定要先进行备份，并且您一定要知道在发生问题时如何还原注册表。 有关如何备份、还原、编辑注册表的信息，请单击下面的文章编号，以便查看 Microsoft 知识库中相应的文章： 256986 （http://support.microsoft.com/kb/256986 Microsoft Windows 注册表说明）

**修改注册表有风险，请提前备份数据并在专业人士指导下慎重操作。**

请通过“**开始**”菜单中的“**运行**”，或通过命令提示符执行“**REGEDIT**”，启动注册表编辑器，然后展开注册表项至：

HKEY\_CURRENT\_USER\\Software\\Microsoft\\Internet Explorer\\Main

右键单击此注册表项，在弹出的右键菜单中选择“**新建**”。您在此既可以选择新注册表项类型为 32 位 DWORD，也可以选择类型为字符串值，然后将新注册表项命名为 TabProcGrowth。

注册表项 TabProcGrowth 负责定义 IE 浏览器启动 IEXPLORE.EXE 进程的方式，随着此注册表项的值不同，IE 浏览器将采用不同的策略运行 IEXPLORE.EXE 进程。如果 TabProcGrowth 不存在，或者即使存在但没有设置任何值，那么 IE 浏览器将继续采用分离 IEXPLORE.EXE 进程、直至达到可用内存与空闲系统资源的上限为止的默认设置。

![](https://webdoc.lenovo.com.cn/lenovowsi/20120806/1344236992544_958.png)

如果您新建 TabProcGrowth 时将类型设置为 DWORD 值，那么您可以按照如下的定义自行设置 TabProcGrowth 的值：

如果 TabProcGrowth 的值被设置为 0，IE 浏览器将不再为主窗口与选项卡分离 IEXPLORE.EXE 进程，每一个 IE 主窗口以及其中的所有选项卡都将合并共用一个 IEXPLORE.EXE 进程。

例如，假设您启动了两个 IE 主窗口，一个主窗口拥有四个选项卡、一个主窗口拥有两个选项卡，Windows 将只启动两个 IEXPLORE.EXE 进程对应这两个 IE 主窗口，而不是启动八个 IEXPLORE.EXE 进程对应两个主窗口及六个选项卡。注意，IE 主窗口的进程不能合并，两个 IE 主窗口无法合并为一个 IEXPLORE.EXE 进程。

而且，在 TabProcGrowth 的值被设置为 0 后，Windows 7/Server 2008（R2）/Vista 将无法以保护模式运行 IE 浏览器，因为 IE 保护模式只能在 IEXPLORE.EXE 进程分离模式中生效。

如果 TabProcGrowth 的值被设置为 1，IE 浏览器将为每个主窗口使用一个分离的 IEXPLORE.EXE 进程，为每个主窗口中的所有选项卡使用一个分离的 IEXPLORE.EXE 进程，但不会为每个单独的选项卡分离 IEXPLORE.EXE 进程。

例如，假设您启动了两个 IE 主窗口，一个主窗口拥有四个选项卡、一个主窗口拥有两个选项卡，Windows 将启动四个 IEXPLORE.EXE 进程。其中两个 IEXPLORE.EXE 进程对应两个 IE 主窗口，另两个 IEXPLORE.EXE 进程分别对应第一主窗口中的四个选项卡与第二主窗口中的两个选项卡。

在 TabProcGrowth 的值被设置为 1 后，Windows 7/Server 2008（R2）/Vista 可以以保护模式运行 IE 浏览器。

如果 TabProcGrowth 的值被设置为任意大于 1 的整数数字（例如 5），IE 浏览器将像默认设置一样为所有的主窗口与选项卡分离 IEXPLORE.EXE 进程，但 IEXPLORE.EXE 进程的总数将不会超过 TabProcGrowth 指定的整数数字。在 IEXPLORE.EXE 进程的数量达到上限后，如果您继续新建选项卡，那么所有的选项卡将按照平均分配的原则共用已经启用的 IEXPLORE.EXE 进程。

在 TabProcGrowth 的值被设置为任意大于 1 的整数数字后，Windows 7/Server 2008（R2）/Vista 可以以保护模式运行 IE 浏览器。

如果您新建 TabProcGrowth 时将类型设置为字符串值，那么您还可以按照如下的定义自行设置 TabProcGrowth 的值：

如果 TabProcGrowth 的值被设置为 small（字符串值），Windows 同时运行的 IEXPLORE.EXE 进程数量将被限制为 5 个。而且，必须至少打开 15 个选项卡才会出现第三个 IEXPLORE.EXE 进程。

如果 TabProcGrowth 的值被设置为 medium（字符串值），Windows 同时运行的 IEXPLORE.EXE 进程数量将被限制为 9 个。而且，必须至少打开 17 个选项卡才会出现第五个 IEXPLORE.EXE 进程。

如果 TabProcGrowth 的值被设置为 large（字符串值），Windows 同时运行的 IEXPLORE.EXE 进程数量将被限制为 16 个。而且，必须至少打开 21 个选项卡才出现第九个 IEXPLORE.EXE 进程。

因此，如果您的计算机可用内存与空闲系统资源紧缺，建议将字符串值类型的 TabProcGrowth 注册表项的值设置为 small 或 medium。

来源：微软知识库 <http://support.microsoft.com/kb/2734435/zh-cn>

<!-- 文档主题：如何控制 Internet Explorer 浏览器的进程数量？ (知识库库编号: 40) -->