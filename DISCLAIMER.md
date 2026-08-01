# Termos de Isenção de Responsabilidade Legal (Disclaimer)

### 1. Isenção de Responsabilidade do Autor
O software **Super Monitor** é fornecido "como está" (*AS IS*), sem qualquer tipo de garantia explícita ou implícita. Em nenhum caso o autor ou desenvolvedores serão responsáveis por quaisquer danos diretos, indiretos, incidentais, especiais ou consequentes resultantes do uso, incapacidade de uso, cópia ou modificações deste código.

### 2. Leitura Não-Invasiva de Sensores
Este software realiza **exclusivamente a leitura passiva** dos sensores de temperatura e velocidade do sistema operacional Linux (`/sys/class/hwmon/`) e envia representações numéricas para a tela do Water Cooler via porta Serial USB. O software **não realiza alterações** no controle de rotação de ventoinhas, bombas, voltagens ou configurações da BIOS do sistema.

### 3. Esclarecimento Sobre o Indicador PUMP Speed
O valor de rotação da bomba (**PUMP Speed**) exibido pela aplicação é resultado de um **cálculo matemático proporcional baseado na rotação da ventoinha (Fan Speed)**. O valor exibido **não é uma medição física direta da bomba de refrigeração líquida**. Para obter a leitura real da velocidade da bomba, o usuário deve utilizar os conectores dedicados da placa-mãe (`PUMP_FAN` / `PUMP_IO`) e adaptar o código conforme necessário.

### 4. Marcas Registradas e Vínculos Corporativos
Todas as marcas registradas, nomes de marcas, nomes de modelos (incluindo *SuperFrame Smart 240mm*), logotipos e patentes mencionadas neste repositório pertencem exclusivamente aos seus respectivos proprietários. A citação de marcas e modelos é feita **única e exclusivamente de forma informativa e descritiva**, com o objetivo de esclarecer a compatibilidade técnica do software, não implicando qualquer tipo de patrocínio, endosso, associação ou vínculo comercial entre o autor do software e as referidas empresas.
