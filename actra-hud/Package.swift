// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "ActraHUD",
    platforms: [
        .macOS(.v14)
    ],
    products: [
        .executable(
            name: "ActraHUD",
            targets: ["ActraHUD"]
        ),
    ],
    dependencies: [],
    targets: [
        .executableTarget(
            name: "ActraHUD",
            dependencies: [],
            path: "Sources/ActraHUD"
        ),
    ]
)
