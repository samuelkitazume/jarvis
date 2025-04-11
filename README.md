## Arquitetura: Assistente Virtual Local (Estilo Jarvis)

### 1. Visão Geral
Um sistema 100% local e modular, com foco em:
- Modelo de linguagem local (LLM)
- Personalidade customizada (prompt ou LoRA)
- Execução de APIs locais (Home Assistant, etc.)
- Memória contextual e raciocínio (via agente ou RAG)
- Integração externa com STT e TTS em outros dispositivos
- Empacotado com Docker Compose para facilitar o deploy

---

### 2. Componentes da Arquitetura

#### 🧠 LLM (Modelo de Linguagem)
- Ex: Mistral 7B, Phi-2, OpenHermes, Nous-Hermes
- Ferramenta: [Ollama](https://ollama.com), LM Studio ou text-generation-webui
- Entrada: Texto do usuário (via STT externo ou texto direto)
- Saída: Resposta textual processada
- Container: `ollama`
- Observação: O Ollama expõe uma API REST em `11434` que pode ser acessada por outros containers ou dispositivos. O LangChain se conecta a ela usando `base_url="http://ollama:11434"` (ou `ollama` como nome de host dentro da rede Docker Compose).

#### 🌟 Personalidade / Estilo de Fala
- Prompt de sistema fixo com instruções de estilo
- (Opcional) LoRA para trejeitos e personalidade
- Configurável via arquivos externos montados como volume

#### 🤹️ Raciocínio + Execução de APIs
- Framework: LangChain, PrivateGPT ou script customizado
- Entrada: Pedido do usuário
- Ação: Interpreta e chama APIs (Home Assistant, etc.)
- Container: `jarvis-backend`
- Integração via OpenAPI Schema: utilizando `langchain.tools.openapi`, é possível importar um schema OpenAPI (ex: do Home Assistant) e permitir que o modelo:
  - Analise os endpoints disponíveis
  - Decida qual usar com base na intenção do usuário
  - Monte automaticamente a requisição HTTP
  - Interprete a resposta da API e gere uma resposta natural
- Observação: Essa funcionalidade atua como uma extensão dos agentes, semelhante a um RAG, mas com foco em ações dinâmicas e integrações externas ao invés de contexto documental.

- **Comparativo RAG vs OpenAPI Agent**:

| Caso de uso                     | Melhor com...        | Justificativa                                      |
|---------------------------------|-----------------------|----------------------------------------------------|
| “Como faço pra resetar a Alexa?”| RAG                   | Informação estável, escrita 1x, útil sempre        |
| “Quantas fraldas hoje de manhã?”| OpenAPI Agent         | Dados variam, dependem de filtros e tempo          |
| “Quais sensores estão ativos?”  | OpenAPI Agent         | Tempo real, consulta dinâmica                      |
| “Qual a rotina ‘Boa noite’?”    | RAG                   | Texto definido e raramente modificado              |
| “Qual foi o último banho?”      | OpenAPI Agent         | Dados estruturados, tempo sensível                 |

---

#### 🤔 Memória e Contexto (RAG)
- Vetor store: Chroma, FAISS, Weaviate
- Uso: Indexa documentos, registros de interação e preferências que sejam essencialmente **estáticos ou com pouca variação**, como FAQs, manuais, instruções da casa, listas de comandos, regras e protocolos.
- Container: `vector-db`
- Observação: O RAG é implementado via LangChain e utiliza o Ollama já existente. Não é iniciado um novo LLM; o LangChain apenas consome a API do Ollama. O processo envolve: carregar documentos, gerar embeddings (ex: MiniLM), armazenar no Chroma e, ao consultar, enviar os trechos recuperados junto com o prompt para o LLM gerar a resposta.
- Limitação: Embora seja eficiente para contexto estático, o RAG não lida bem com **dados altamente dinâmicos** (como logs atualizados, sensores, e-mails, atividades de bebê, etc.), onde o uso de **agentes com integração via OpenAPI** é mais apropriado e flexível.
- Recomendação: Use RAG para dados de referência duradouros (manuais, comandos, regras fixas), e agentes para dados vivos ou em constante mutação.

---

### 3. Fluxo de Dados Modular

**[Dispositivo Externo]**
1. STT (Speech-to-text)
2. Envia prompt para API da LLM (Kali Linux)

**[Servidor Kali Linux]**
3. LLM interpreta comando + aplica personalidade
4. Agente decide se chama API (via OpenAPI) ou responde direto
5. (Opcional) Consulta ao vetor store (RAG)
6. Resposta textual é devolvida pela API

**[Dispositivo Externo]**
7. Recebe resposta textual
8. TTS gera voz e reproduz

---

### 4. Requisitos de Hardware

#### ⚡ Setup Modesto (sem RAG, modelo menor)
- CPU com 4+ threads
- 8 GB RAM
- SSD 256 GB+
- (Opcional) GPU integrada ou modesta (Intel UHD, AMD Vega)
- Modelo: Phi-2, Mistral 7B quantizado (Q4)

#### 🔥 Setup Intermediário (com RAG)
- CPU 6+ cores
- 16 GB RAM
- SSD 512 GB+
- GPU com 8-12 GB VRAM (ex: RTX 3060, 4060)
- Modelo: Mistral 7B, Nous Hermes, OpenHermes
- Vector DB para contexto

#### 🌌 Setup Avançado (conhecimento, alta fluidez)
- CPU 8+ cores
- 32 GB RAM
- SSD 1 TB NVMe
- GPU com 24+ GB VRAM (ex: RTX 4090)
- Modelo: Mixtral 8x7B, MythoMax 13B, LLaMA 2 13B+
- RAG com banco vetorial completo

---

### 5. Justificativa Arquitetural: Separar STT/TTS do LLM
- A separação de responsabilidades permite que o servidor Kali Linux atue como "cérebro" central (LLM + RAG), enquanto outro dispositivo lida com voz (STT/TTS)
- Em redes locais, a latência é baixíssima e praticamente imperceptível (<5ms)
- O TTS pode ser rodado em um desktop com GPU (ou mesmo CPU) sem sobrecarregar o backend
- TTSs mais pesados como Bark ou Tortoise podem ser processados offline e reproduzidos via rede
- A arquitetura facilita atualizações, manutenção e expansão futura para vários dispositivos

---

### 6. Expansões Futuras
- Controle por gesto ou câmera
- Fine-tuning com dados pessoais (LoRA customizado)
- Multiusuário com identificação de voz
- Dashboard web com logs + comandos
- Interface visual tipo "Jarvis HUD"
- Gerenciamento dos containers via WebUI
- Distribuição modular com vários dispositivos em rede


### Dicas

#### Curl para jarvis-backend
```bash
curl -X POST http://localhost:5000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Hey, Jarvis!"}'
```

#### Curl para Ollama direto
```bash
curl http://localhost:11434/api/generate \
  -d '{
    "model": "phi",
    "prompt": "What is the capital of Canada?",
    "stream": false
  }' \
  -H "Content-Type: application/json"
```

