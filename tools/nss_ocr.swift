
import Vision
import AppKit
import Foundation

let args = CommandLine.arguments
guard args.count > 1 else {
    print("Usage: nss_ocr <image_path>")
    exit(1)
}

let imagePath = args[1]
guard let image = NSImage(contentsOfFile: imagePath),
      let tiffData = image.tiffRepresentation,
      let bitmap = NSBitmapImageRep(data: tiffData),
      let cgImage = bitmap.cgImage else {
    print("ERROR: Cannot load \(imagePath)")
    exit(1)
}

let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.recognitionLanguages = ["en", "ko"]
request.usesLanguageCorrection = true

let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
try handler.perform([request])

guard let observations = request.results else { exit(1) }
for obs in observations {
    if let c = obs.topCandidates(1).first {
        print(c.string)
    }
}
