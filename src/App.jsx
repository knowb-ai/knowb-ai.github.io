import { useState } from 'react'

function App() {
  const [activeSection, setActiveSection] = useState('home')

  const scrollToSection = (sectionId) => {
    const element = document.getElementById(sectionId)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' })
      setActiveSection(sectionId)
    }
  }

  const projects = [
    {
      title: "kenobi",
      description: "Knowledge-Base-as-a-Service (KbaaS) prototype inspired by the Kenobi—secure, extensible, and ready for the Jedi in every org."
    },
    {
      title: "PostPilot",
      description: "An open-source automation engine that turns your Notion board into a full-blown AI-powered content pipeline. Ideas go in. RAG-fueled drafts come out. You review, approve, and schedule — we post. Built with ✨ Notion + 🧠 OpenAI + ⚙️ n8n."
    },
    {
      title: "XPosay",
      description: "XPosay: Because lies don't fact-check themselves. A real-time fact-checking toolkit powered by LLMs and curated knowledge databases to counter disinformation with receipts."
    },
    {
      title: "Disqus",
      description: "A place for students to transform a pitch into a full project assisted by AI agents and allow discussion of features and people interested to help evolve the idea via comments."
    },
    {
      title: "CouplesThereAI.py",
      description: "A whisper voice activated LLM agent that will facilitate couples therapy and counselling sessions."
    }
  ]

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-gray-950/80 backdrop-blur-md border-b border-gray-800">
        <nav className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="text-xl font-semibold tracking-tight">knowb.run</div>
          <div className="flex gap-8 text-sm">
            <button onClick={() => scrollToSection('home')} className="hover:text-white transition-colors">Home</button>
            <button onClick={() => scrollToSection('what-are')} className="hover:text-white transition-colors">What Are Knowledge Agents</button>
            <button onClick={() => scrollToSection('projects')} className="hover:text-white transition-colors">Projects</button>
            <button onClick={() => scrollToSection('contact')} className="hover:text-white transition-colors">Contact</button>
          </div>
        </nav>
      </header>

      {/* Hero Section */}
      <section id="home" className="pt-32 pb-20 px-6">
        <div className="max-w-5xl mx-auto text-center">
          <h1 className="text-6xl font-bold mb-6 tracking-tight">
            The Home of Knowledge Agents
          </h1>
          <p className="text-xl text-gray-400 mb-12 max-w-3xl mx-auto leading-relaxed">
            Systems that unify foundational AI models, curated expert KnowledgeBases, and real-world context — delivering intelligence that is accurate, adaptive, and purpose-built.
          </p>
          <div className="flex gap-4 justify-center">
            <button 
              onClick={() => scrollToSection('what-are')}
              className="px-8 py-3 bg-white text-gray-950 rounded-lg font-medium hover:bg-gray-200 transition-all"
            >
              What Are Knowledge Agents?
            </button>
            <button 
              onClick={() => scrollToSection('projects')}
              className="px-8 py-3 border border-gray-700 rounded-lg font-medium hover:bg-gray-900 transition-all"
            >
              Explore Projects
            </button>
          </div>
        </div>
      </section>

      {/* What Are Knowledge Agents */}
      <section id="what-are" className="py-20 px-6 bg-gray-900/50">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-4xl font-bold mb-16 text-center">What Are Knowledge Agents?</h2>
          
          <div className="mb-16 text-lg text-gray-300 leading-relaxed max-w-4xl mx-auto">
            <p className="mb-6">
              Knowledge Agents are intelligent systems that combine three layers of knowledge to deliver precise, context-aware results:
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 mb-16">
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 hover:border-gray-700 transition-all">
              <div className="text-3xl font-bold text-white mb-4">1</div>
              <h3 className="text-xl font-semibold mb-4">General Knowledge</h3>
              <p className="text-gray-400 leading-relaxed">
                Derived from foundation models such as GPT-4o, Claude, and Gemini, enriched with real-time web search. 
                This layer handles broad reasoning, world knowledge, language fluency, and general problem-solving.
              </p>
            </div>

            <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 hover:border-gray-700 transition-all">
              <div className="text-3xl font-bold text-white mb-4">2</div>
              <h3 className="text-xl font-semibold mb-4">Specialized Knowledge (KnowledgeBases)</h3>
              <p className="text-gray-400 leading-relaxed">
                Custom curated sources of expert, specialized, or recent information. 
                These KnowledgeBases encode domain-specific expertise, rules, workflows, and industry-level accuracy needed for a special-purpose task.
              </p>
            </div>

            <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 hover:border-gray-700 transition-all">
              <div className="text-3xl font-bold text-white mb-4">3</div>
              <h3 className="text-xl font-semibold mb-4">Context and Use-Case Knowledge</h3>
              <p className="text-gray-400 leading-relaxed">
                Awareness of where the knowledge is being applied. 
                This includes personalization, user preferences, local constraints, task requirements, and environment-specific parameters. 
                This layer ensures outputs are not generic — but specifically tailored, accurate, and relevant.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Why This Matters */}
      <section className="py-20 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold mb-8">Why This Matters</h2>
          <p className="text-xl text-gray-300 leading-relaxed">
            Knowledge Agents transform raw AI intelligence into operational intelligence. 
            By combining general reasoning, expert knowledge, and contextual awareness, they produce results that are actionable, reliable, and aligned to the real world.
          </p>
        </div>
      </section>

      {/* How Knowledge Agents Work */}
      <section className="py-20 px-6 bg-gray-900/50">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-4xl font-bold mb-16 text-center">How Knowledge Agents Work</h2>
          
          <div className="space-y-8">
            <div className="flex gap-6 items-start">
              <div className="flex-shrink-0 w-16 h-16 bg-white text-gray-950 rounded-lg flex items-center justify-center text-xl font-bold">
                1
              </div>
              <div>
                <h3 className="text-2xl font-semibold mb-3">Understand</h3>
                <p className="text-gray-400 text-lg leading-relaxed">
                  The agent interprets the user's prompt, intent, context, constraints, and local settings.
                </p>
              </div>
            </div>

            <div className="flex gap-6 items-start">
              <div className="flex-shrink-0 w-16 h-16 bg-white text-gray-950 rounded-lg flex items-center justify-center text-xl font-bold">
                2
              </div>
              <div>
                <h3 className="text-2xl font-semibold mb-3">Retrieve</h3>
                <p className="text-gray-400 text-lg leading-relaxed">
                  It queries the appropriate KnowledgeBases — curated expert knowledge, recent data, or specialized information relevant to the task.
                </p>
              </div>
            </div>

            <div className="flex gap-6 items-start">
              <div className="flex-shrink-0 w-16 h-16 bg-white text-gray-950 rounded-lg flex items-center justify-center text-xl font-bold">
                3
              </div>
              <div>
                <h3 className="text-2xl font-semibold mb-3">Synthesize & Act</h3>
                <p className="text-gray-400 text-lg leading-relaxed">
                  The agent combines foundation model reasoning, retrieved domain knowledge, and contextual personalization to deliver a tailored output or execute an action.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Projects Gallery */}
      <section id="projects" className="py-20 px-6">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-4xl font-bold mb-4 text-center">Knowledge Agents in Practice</h2>
          <p className="text-center text-gray-400 mb-16 text-lg">Real-world implementations of the Knowledge Agent paradigm</p>
          
          <div className="grid md:grid-cols-2 gap-6">
            {projects.map((project, index) => (
              <div 
                key={index} 
                className="bg-gray-900 border border-gray-800 rounded-xl p-8 hover:border-gray-600 transition-all hover:shadow-xl hover:shadow-gray-900/50"
              >
                <h3 className="text-2xl font-semibold mb-4">{project.title}</h3>
                <p className="text-gray-400 leading-relaxed">{project.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer id="contact" className="border-t border-gray-800 py-12 px-6 mt-20">
        <div className="max-w-6xl mx-auto text-center text-gray-500">
          <p className="mb-4">© 2025 knowb.run</p>
          <p className="mb-4">Contact: <span className="text-gray-400">hello@knowb.run</span></p>
          <div className="flex gap-4 justify-center text-sm">
            <a href="#" className="hover:text-gray-300 transition-colors">Terms</a>
            <span>·</span>
            <a href="#" className="hover:text-gray-300 transition-colors">Privacy</a>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App
