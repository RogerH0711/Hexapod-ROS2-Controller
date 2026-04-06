# 🕷️ Hexapod-ROS2-Controller: 12-DOF 機器人軟硬體整合控制系統

![ROS 2](https://img.shields.io/badge/ROS_2-Humble-blue.svg) 
![Python](https://img.shields.io/badge/Python-3.8+-yellow.svg)
![Platform](https://img.shields.io/badge/Platform-ESP32-lightgrey.svg)
![Award](https://img.shields.io/badge/Award-1st_Place_in_ICTDE-gold.svg)

> 本專案為國立成功大學114-1「數位電路導論」課程期末專題第一名作品。
> 透過整合 ROS 2 框架與 ESP32 微控制器，實現 12 自由度（12-DOF）六足機器人的低延遲步態控制與即時運動學解算，展現軟硬體協同設計 (Hardware-Software Co-design) 之系統架構能力。

## 🎥 System Demonstration (動態展示)
點擊 GIF 即可跳轉至 YouTube 觀看完整展示影片：
[![Hexapod Demo](https://github.com/user-attachments/assets/bb4db6a3-ee62-4f9b-b1e7-5472a5d9b68e)](https://youtu.be/VLPHDPNgL0g)

---

## 🏗️ System Architecture (系統架構與全機視角)

本專案採用**軟硬體解耦**的設計思維，將上層的演算法邏輯與底層的硬體驅動分離，以確保系統的高擴充性與穩定度。

<p align="center">
  <img src="https://github.com/user-attachments/assets/396aaf5b-394f-4dcf-a906-0b74dd5aedd9" alt="Full Robot View" width="500">
</p>

```text
[ Upper Level: ROS 2 / PC ]
 ├── 🧠 Gait Controller (run_publisher_final.py)  <-- 本專案核心演算法
 │    ├── Multi-threading Keyboard Listener (異步指令接收)
 │    └── Tripod Gait Generator (三角步態軌跡計算)
 │
 └── 📡 Bus Servo Driver Node (依賴庫整合)
      └── Translates JointTrajectory to Serial Packets

[ Lower Level: Hardware / ESP32 ]
 ├── 🔌 ESP32 Microcontroller (Firmware: Serial Parsing & PWM)
 └── ⚙️ 12 x Hiwonder Serial Bus Servos
```
-----

## 🛠️ Hardware Specifications (硬體與零件選型)

為了達成高精度的步態控制與穩定的系統供電，本專案在硬體選型與佈線上經過嚴格評估，實現動力電源與邏輯電源的穩定分配。

| Component (零件名稱) | Specification / Model (規格型號) | Purpose in System (系統用途) |
| :--- | :--- | :--- |
| **Microcontroller** | Bus Servo Driver HAT (A) with **ESP32-WROOM-32E** | 擔任底層核心硬體，負責解析 ROS 2 傳來的串列封包，並生成對應的控制訊號。利用其雙核心與高時脈優勢處理即時控制。 |
| **Actuators** | **Hiwonder** Serial Bus Servos (45kg.cm High Torque) x 12 | 提供 12 自由度的關節動力。採用串列匯流排馬達而非傳統 PWM 馬達，大幅減少配線複雜度，並支援角度回讀功能。 |
| **Power Supply** | 12V / 10A AC/DC Adapter| 為 12 顆高扭力伺服馬達提供瞬間大電流，確保多軸連動時不會因壓降而導致控制器重啟。 |
| **Structure** | Custom Hexapod Frame | 六足機器人實體機構支撐，確保多軸連動時的結構剛性與幾何對稱性。 |
<p align="center">
  <img src="https://github.com/user-attachments/assets/a7653139-2633-4227-a940-65b92d0868f8" alt="Hardware Board" width="45%">
  <img src="https://github.com/user-attachments/assets/8e1fcf93-48db-4223-8cf7-252d6949433c" alt="Serial Bus Servos" width="45%">
</p>
-----

## 💻 Core Contribution: Gait Controller

本 Repository 的核心貢獻為 `src/run_publisher_final.py`，負責六足機器人的大腦運算。主要技術亮點包含：

1.  **非同步多執行緒設計 (Multi-threading with Locks)**
    導入 `threading.Thread` 與 `threading.Lock()`，將「鍵盤指令監聽」與「步態運動主循環」分離。確保在進行複雜的三角步態（Tripod Gait）計算與發布時，系統仍能零延遲地響應使用者的中斷或轉向指令。
2.  **ROS 2 Trajectory Publishing**
    將計算出的各關節角度，封裝成標準的 `JointTrajectory` 訊息格式，並精準控制時間戳記（250ms 發布週期），確保實體馬達運作平滑不抖動。
3.  **動態三角步態演算法 (Dynamic Tripod Gait)**
    將 6 條腿分為兩組（Tripod 1 & Tripod 2），透過狀態機邏輯，實現流暢的前進、後退與原地轉向，並保留了 `LIFT_OFFSET` 與 `PAN_OFFSET` 的參數化設計，方便未來導入動態調整演算法。

-----

## 🔗 Hardware & Dependencies (硬體與底層驅動依賴)

本專案的成功運作，建立在以下優秀的開源驅動與工具庫之上。感謝以下 Repository 提供底層的通訊與校正支援：

  * **[zlink-bus-servo-driver](https://github.com/alianlbj23/zlink-bus-servo-driver.git)**
    作為 ROS 2 與匯流排馬達之間的通訊橋樑，負責處理底層的封包轉換與序列埠發送。
  * **[ESP32\_servo\_control](https://github.com/Steven0811/ESP32_servo_control.git)**
    燒錄於 ESP32 的韌體核心，負責接收上位機指令並輸出高精度的 PWM 訊號至 12 顆伺服馬達。
  * **[tools](https://github.com/screamlab/tools.git)**
    用於機器人組裝初期的零點校正與環境變數建置。

-----

## 🚀 How to Run (執行方式)

### 1. Environment Setup

請確保已安裝 ROS 2 (Humble/Foxy) 並編譯上述依賴庫的工作區 (Workspace)。

### 2. Launching the Controller

```bash
# 啟動底層通訊節點 (依賴庫)
ros2 launch zlink_bus_servo_driver bus_servo_driver.launch.py

# 啟動本專案之步態控制大腦
python3 src/run_publisher_final.py
```

### 3\. Controls

  * `W` : 前進 (Walk Forward)
  * `S` : 後退 (Walk Backward)
  * `A` : 原地左轉 (Turn Left)
  * `D` : 原地右轉 (Turn Right)
  * `[Space]` : 停止並回到站立姿態 (Stand)
  * `Q` : 安全退出程式 (Quit)

<!-- end list -->
