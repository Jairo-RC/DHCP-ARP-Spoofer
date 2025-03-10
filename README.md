# 🚀 DHCP Spoofing Attack Tool

This script is a **Python GUI application** that allows performing **DHCP Spoofing attacks** using `Yersinia`. It floods the network with rogue DHCP offers, potentially disrupting network access.

⚠ **Legal Notice:** This tool is intended for educational and testing purposes only in controlled environments. Unauthorized use of this software is illegal and can result in severe consequences.

---

## 📌 Features

✅ Simple GUI for executing DHCP Spoofing attacks.  
✅ Automatic detection of the active network interface.  
✅ Real-time attack execution with output display.  
✅ One-click attack start and stop functionality.  

---

## 📦 Installation

### 🔹 Prerequisites
Ensure you have Python 3 installed on your system and install the required dependencies:

```bash
pip install tkinter
```

Additionally, you need `Yersinia`, a network attack tool. Install it using:

```bash
sudo apt install yersinia
```

💡 **Note:** This script is intended for **Linux-based systems**. Ensure you have root privileges when running the script.

---

## 🚀 Usage

1️⃣ **Run the script with root privileges**

```bash
sudo python dhcp_spoof.py
```

2️⃣ **Start the attack**
- Click the **"Start Attack"** button to begin the DHCP spoofing attack.
- The attack floods the network with fake DHCP responses, potentially disrupting normal connectivity.

3️⃣ **Stop the attack**
- Click **"Stop Attack"** to terminate the process.
- The script will stop `Yersinia` and restore network functionality.

---

## 🖥 Screenshots

🚧 *(Coming soon: Add screenshots of the application interface for better clarity.)* 🚧

---

## ⚠ Warning

Using this tool on unauthorized networks is **illegal** and may lead to legal consequences. Only use it for testing in controlled environments.

---

## 📜 License

This project is distributed under the MIT license. You are free to modify and use the code for educational and research purposes.

🚀 **Use responsibly and ethically!**
