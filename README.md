# Skynet Knowledge Engine 🚀

**Team Major Tom** | NASA SpaceApps Hackathon 2025 | Victoria, BC

An AI-powered semantic search and summarization platform for NASA's Space Biology research papers. Built for researchers, funding managers, and students to quickly discover and understand insights from 600+ scientific publications.

---

## 🌟 What is Skynet Knowledge Engine?

Skynet Knowledge Engine transforms how people interact with NASA's vast collection of space biology research. Instead of manually sifting through hundreds of papers, users can:

- **Ask natural language questions** and get relevant research instantly
- **Receive AI-generated summaries** tailored to their role (Researcher, Manager, or Student)
- **Explore 11,460+ document chunks** from 608 NASA publications
- **Continue conversations** with follow-up questions to dive deeper

### Key Features

- **Role-Based Summaries**: Customized AI responses based on whether you're a researcher (technical detail), funding manager (applications/impact), or student (educational focus)
- **Semantic Search**: Powered by OpenAI embeddings and summaries
- **Interactive Chat**: Ask follow-up questions and build on previous answers
- **Beautiful UI**: Modern, space-themed interface with smooth animations

---

## 🎯 Use Cases

### For Researchers
*"What are the effects of microgravity on bone density?"*
- Get detailed methodologies, numerical results, and experimental designs
- Discover research gaps and potential collaboration opportunities

### For Funding Managers
*"What are the commercial applications of plant research in space?"*
- Understand real-world impact and funding opportunities
- See which research areas have the most potential for development

### For Students
*"How does radiation affect astronauts?"*
- Learn fundamentals with clear, accessible explanations
- Build foundational knowledge for future studies

---

## 🏗️ Tech Stack

**Frontend**
- HTML5, CSS3, JavaScript (Vanilla)
- Space-themed UI with custom animations

**Backend**
- Python 3.12
- Flask (Web framework)
- OpenAI GPT-4o-mini (Summarization & embeddings)
- scikit-learn (Cosine similarity)

**Data**
- 608 NASA Space Biology publications
- 11,460 pre-processed document chunks
- Pre-computed OpenAI embeddings

---

## 🚀 Getting Started

### Prerequisites

- Python 3.12 or higher
- OpenAI API key 
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/nasa-hackathon-2025.git
   cd nasa-hackathon-2025
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   


4. **Set up environment variables**
   
   Create a `.env` file in the project root:
   ```bash
   OPENAI_API_KEY=your-api-key-here
   ```

5. **Run the application**
   ```bash
   python backend.py
   ```

6. **Open your browser**
   
   Navigate to: `http://localhost:5000`

---

## 📖 How to Use

### Step 1: Select Your Role
When you first open the app, choose your role:
- **Researcher/Scientist** → Technical, detailed summaries
- **Manager/Investor** → Focus on applications and impact

### Step 2: Search
Enter your question in natural language:
- "What are the effects of radiation on plants in space?"
- "How does microgravity affect the immune system?"
- "What changes occur in gene expression during spaceflight?"

### Step 3: Explore Results
- View the AI-generated summary with key findings
- See the top 5 most relevant research papers
- Read direct excerpts from the source documents

### Step 4: Ask Follow-ups
Continue the conversation by asking related questions:
- "What were the specific measurements used?"
- "Are there any commercial applications?"
- "What are the main research gaps?"

---

## 📁 Project Structure

```
nasa-hackathon-2025/
├── backend.py                 # Flask server & API routes
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (you create this)
│
├── frontendwebsetup/          # Web interface
│   ├── role.html             # Role selection page
│   ├── search.html           # Search interface
│   ├── results.html          # Results & chat interface
│   └── *.jpg                 # Images and assets
│
├── src/                       # Core logic
│   ├── search_and_rank.py    # Semantic search engine
│   ├── summarize_openai.py   # AI summarization
│   ├── build_chunks.py       # Document preprocessing
│   ├── build_index_openai.py # Embedding generation
│   └── ...
│
├── models/                    # Pre-built indexes & embeddings
│   ├── emb_full_chunks.jsonl # Document chunks (11,460)
│   ├── emb_full.npy          # Precomputed embeddings
│   └── ...
│
└── data/                      # Raw source data
    └── SB_publication_PMC.csv
```

---

## 🔬 How It Works

### 1. **Document Preprocessing**
- NASA papers are fetched, parsed, and chunked into semantic units
- Each chunk contains ~500-1000 tokens of context

### 2. **Embedding Generation**
- OpenAI's `text-embedding-3-small` model creates vector representations
- Embeddings are pre-computed and stored for fast retrieval

### 3. **Semantic Search**
- User query is embedded using the same model
- Cosine similarity is used to find most similar chunks
- Results are ranked by relevance score

### 4. **AI Summarization**
- Top chunks are sent to GPT-4o-mini with role-specific prompts
- AI synthesizes findings, not just summarizing each paper individually
- Response includes key findings, applications, and top sources

### 5. **Interactive Chat**
- Conversation history is maintained
- Follow-up questions use context from previous exchanges

---

## 🎓 NASA SpaceApps Challenge

**Challenge**: [NASA Space Apps Hackathon 2025]

**Team Major Tom**
- Built during the 2025 NASA SpaceApps Hackathon
- Local event: Victoria, BC, Canada

### Problem Statement
Researchers, students, and funding managers struggle to efficiently navigate NASA's extensive space biology research archives. Finding relevant studies and synthesizing findings across multiple papers is time-consuming and complex.

### Our Solution
Skynet Knowledge Engine democratizes access to space biology research through:
- Natural language queries that feel like asking a colleague
- AI-powered synthesis that connects insights across studies
- Role-based customization for different user needs

---


## 🛠️ Technical Highlights

- **Fast Searches*: The system uses scikit-learn's cosine similarity
- **Efficient Embeddings**: Pre-computed OpenAI embeddings eliminate real-time processing delays
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Conversation Memory**: Maintains chat history for coherent follow-up questions

---

## 📊 Dataset

**Source**: NASA Space Biology Publications (PubMed Central)
- 608 total publications
- 11,460 semantic chunks
- Topics include: microgravity effects, radiation biology, plant biology, animal studies, cellular mechanisms, and more

---

## 🙏 Acknowledgments

- **NASA** for providing open access to space biology research
- **OpenAI** for GPT-4o-mini and embedding models
- **NASA SpaceApps Challenge** for the inspiring hackathon
- **Our team** for 48 hours of caffeine-fueled coding

---

## 📄 License

This project was created for the NASA SpaceApps Hackathon 2025.

---

## 🌠 Future Enhancements

- Export results to PDF or citation format
- Visualization of research trends over time
- Integration with more NASA databases
- Multi-language support
- Advanced filtering by publication date, topic, or research type

---

**Built with ❤️ and 🚀 by Team Major Tom**
