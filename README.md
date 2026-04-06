# 🕷️ Hexapod-ROS2-Controller: 12-DOF 機器人軟硬體整合控制系統

![ROS 2](https://img.shields.io/badge/ROS_2-Humble-blue.svg) 
![Python](https://img.shields.io/badge/Python-3.8+-yellow.svg)
![Platform](https://img.shields.io/badge/Platform-ESP32-lightgrey.svg)
![Award](https://img.shields.io/badge/Award-1st_Place_in_Digital_Circuit_Design-gold.svg)

> 本專案為國立成功大學114-1「數位電路導論」課程期末專題第一名作品。
> 透過整合 ROS 2 框架與 ESP32 微控制器，實現 12 自由度（12-DOF）六足機器人的低延遲步態控制與即時運動學解算，展現軟硬體協同設計 (Hardware-Software Co-design) 之系統架構能力。

## 🎥 System Demonstration (動態展示)

[![Hexapod Demo](https://github.com/user-attachments/assets/bb4db6a3-ee62-4f9b-b1e7-5472a5d9b68e)](https://youtu.be/VLPHDPNgL0g)

---

## 🏗️ System Architecture (系統架構與全機視角)

本專案採用**軟硬體解耦**的設計思維，將上層的演算法邏輯與底層的硬體驅動分離，以確保系統的高擴充性與穩定度。

![Full Robot View](https://github.com/user-attachments/assets/396aaf5b-394f-4dcf-a906-0b74dd5aedd9)

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
