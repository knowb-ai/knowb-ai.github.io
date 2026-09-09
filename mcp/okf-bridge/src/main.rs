//! Private JSON adapter for the pinned okf-rs search library.
use serde::Deserialize;
use serde_json::json;
use std::{
    io::{self, Read},
    path::PathBuf,
};

const PROTOCOL: u8 = 1;
const ADAPTER_VERSION: &str = "0.2.0";
const OKF_RS_REVISION: &str = "6d52cc7ad0b5afea2e0001779b4498e268905ddc";
const BUILD_TARGET: &str = env!("KNOWB_BUILD_TARGET");
const MAX_REQUEST_BYTES: usize = 65_536;
const MAX_QUERY_BYTES: usize = 16_384;
const MAX_RESULTS: usize = 50;
const MAX_DOCUMENTS: usize = 10_000;

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Request {
    bundle: PathBuf,
    query: String,
    limit: usize,
    documents: usize,
}

fn info() -> serde_json::Value {
    json!({
        "protocol": PROTOCOL,
        "adapter_version": ADAPTER_VERSION,
        "okf_rs_revision": OKF_RS_REVISION,
        "build_target": BUILD_TARGET,
        "max_request_bytes": MAX_REQUEST_BYTES,
        "max_query_bytes": MAX_QUERY_BYTES,
        "max_results": MAX_RESULTS,
    })
}

fn run() -> Result<(), Box<dyn std::error::Error>> {
    match std::env::args().nth(1).as_deref() {
        Some("--info") => {
            println!("{}", info());
            return Ok(());
        }
        Some("--version") => {
            println!("knowb-okf-bridge {ADAPTER_VERSION} (okf-rs {OKF_RS_REVISION})");
            return Ok(());
        }
        _ => {}
    }
    let mut input = String::new();
    io::stdin()
        .take((MAX_REQUEST_BYTES + 1) as u64)
        .read_to_string(&mut input)?;
    if input.len() > MAX_REQUEST_BYTES {
        return Err("request exceeds 64 KiB".into());
    }
    let request: Request = serde_json::from_str(&input)?;
    if request.query.len() > MAX_QUERY_BYTES {
        return Err("query exceeds 16 KiB".into());
    }
    if request.documents > MAX_DOCUMENTS {
        return Err("document count exceeds adapter limit".into());
    }
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
    let hits = index.search(&request.query, request.limit.clamp(1, MAX_RESULTS))?;
    let results: Vec<_> = hits
        .iter()
        .map(|hit| json!({"id": hit.id, "score": hit.score}))
        .collect();
    let output = json!({"protocol": PROTOCOL, "results": results}).to_string();
    if output.len() > MAX_REQUEST_BYTES {
        return Err("response exceeds 64 KiB".into());
    }
    println!("{output}");
    Ok(())
}

fn main() {
    if let Err(error) = run() {
        let message = error.to_string();
        let bounded = if message.len() > 1500 {
            &message[..1500]
        } else {
            &message
        };
        eprintln!("knowb-okf-bridge: {bounded}");
        std::process::exit(1);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn info_contains_protocol_contract() {
        let value = info();
        assert_eq!(value["protocol"], PROTOCOL);
        assert_eq!(value["adapter_version"], ADAPTER_VERSION);
        assert_eq!(value["okf_rs_revision"], OKF_RS_REVISION);
        assert_eq!(value["build_target"], BUILD_TARGET);
        assert_eq!(value["max_request_bytes"], MAX_REQUEST_BYTES);
        assert_eq!(value["max_query_bytes"], MAX_QUERY_BYTES);
        assert_eq!(value["max_results"], MAX_RESULTS);
    }
}
