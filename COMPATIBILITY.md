# Tabela de Compatibilidade e Requisitos de Hardware

## 🖥️ Water Coolers Suportados

| Modelo / Marca | Status de Testes | Observações |
| :--- | :---: | :--- |
| **SuperFrame Smart 240mm (Bomba Infinity)** | 🟢 Testado e Aprovado | Comunicação Serial via CH340/CH341 nativa. |
| Outros Water Coolers com telas LCD/LED via USB CH340/CH341 | 🟡 Compatível (Teórico) | Requer protocolo de comando compatível (`0x01` para Temp/RPM). |

---

## 🔌 Controladores Serial USB (VID / PID)

| Chipset | Vendor ID (VID) | Product ID (PID) | Suporte no Script |
| :--- | :---: | :---: | :---: |
| QinHeng Electronics CH340 | `0x1A86` | `0x7523` / `0x7584` | ✅ Autodetectado |
| QinHeng Electronics CH341 | `0x1A86` | `0x5523` / `0x5512` | ✅ Autodetectado |

---

## 🐧 Compatibilidade de Sensores do Kernel Linux

O script lê a temperatura média procurando pelos drivers de hwmon padrão:
- **Intel:** `coretemp`
- **AMD:** `k10temp`, `zenpower`

As ventoinhas são identificadas via entradas `/sys/class/hwmon/hwmon*/fan*_input`.
