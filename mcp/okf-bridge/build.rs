fn main() {
    let target = std::env::var("TARGET").expect("Cargo must provide TARGET to build scripts");
    println!("cargo:rustc-env=KNOWB_BUILD_TARGET={target}");
    println!("cargo:rerun-if-env-changed=TARGET");
}
