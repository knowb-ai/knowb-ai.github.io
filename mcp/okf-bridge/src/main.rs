//! Private JSON adapter for the pinned okf-rs search library.
use serde::Deserialize;
use serde_json::json;
use std::{
    io::{self, Read},
    path::PathBuf,
};

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Request {
    bundle: PathBuf,
    query: String,
    limit: usize,
    documents: usize,
}

fn run() -> Result<(), Box<dyn std::error::Error>> {
    if std::env::args().nth(1).as_deref() == Some("--version") {
        println!("knowb-okf-bridge 0.1.0 (okf-rs 6d52cc7ad0b5afea2e0001779b4498e268905ddc)");
        return Ok(());
    }
    let mut input = String::new();
    io::stdin().take(65537).read_to_string(&mut input)?;
    if input.len() > 65536 {
        return Err("request exceeds 64 KiB".into());
    }
    let request: Request = serde_json::from_str(&input)?;
    let mut concepts = okf_parser::read_bundle(&request.bundle)?;
    // Upstream skips unsupported/malformed concepts. Never silently lose documents.
    if concepts.len() != request.documents {
        return Err("bundle document count mismatch".into());
    }
    for concept in &mut concepts {
        let text = std::fs::read_to_string(request.bundle.join(format!("{}.md", concept.id)))?;
        let (_, body) = text
            .split_once("\n---\n")
            .ok_or("missing frontmatter delimiter")?;
        // Upstream indexes descriptions/signatures, not arbitrary Markdown bodies.
        // Supply full documentation text in memory without altering source metadata.
        concept.description = Some(body.to_owned());
    }
    let index = okf_search::FullTextIndex::build_from_concepts(&concepts)?;
    let hits = index.search(&request.query, request.limit.clamp(1, 50))?;
    let results: Vec<_> = hits
        .iter()
        .map(|hit| json!({"id": hit.id, "score": hit.score}))
        .collect();
    println!("{}", json!({"protocol": 1, "results": results}));
    Ok(())
}

fn main() {
    if let Err(error) = run() {
        eprintln!("knowb-okf-bridge: {error}");
        std::process::exit(1);
    }
}
