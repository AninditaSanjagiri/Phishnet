"""
train_image_model.py
====================
Fine-tune MobileNetV3-Small on phishing vs legitimate screenshots.

Dataset structure expected:
  data/screenshots/
    phishing/   ← screenshots of phishing pages
    legitimate/ ← screenshots of legitimate pages

How to build the dataset:
  1. Get phishing URLs from PhishTank
  2. Run: python capture_screenshots.py --urls phish_urls.txt --output data/screenshots/phishing
  3. Use Tranco top-1k for legit screenshots similarly

Usage:
  python train_image_model.py --data data/screenshots --epochs 10 --output models/image_mobilenet.pth
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/screenshots", help="Root dataset directory")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--output", default="models/image_mobilenet.pth")
    args = parser.parse_args()

    try:
        import torch
        import torch.nn as nn
        from torch.utils.data import DataLoader
        from torchvision import datasets, transforms
        from torchvision.models import mobilenet_v3_small, MobileNet_V3_Small_Weights
    except ImportError:
        print("❌ Install: pip install torch torchvision")
        sys.exit(1)

    data_path = Path(args.data)
    if not data_path.exists():
        print(f"❌ Dataset not found at {data_path}")
        print("   Create: data/screenshots/phishing/ and data/screenshots/legitimate/")
        sys.exit(1)

    # Transforms
    train_tf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    val_tf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])

    # Dataset (80/20 split)
    full_ds = datasets.ImageFolder(str(data_path), transform=train_tf)
    n_val = int(len(full_ds) * 0.2)
    n_train = len(full_ds) - n_val
    train_ds, val_ds = torch.utils.data.random_split(full_ds, [n_train, n_val])
    val_ds.dataset.transform = val_tf

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, num_workers=2)

    print(f"Dataset: {n_train} train / {n_val} val")
    print(f"Classes: {full_ds.classes}")

    # Model — transfer learning from ImageNet
    model = mobilenet_v3_small(weights=MobileNet_V3_Small_Weights.DEFAULT)
    in_features = model.classifier[-1].in_features
    model.classifier[-1] = nn.Linear(in_features, 2)

    # Freeze feature extractor for first 3 epochs
    for param in model.features.parameters():
        param.requires_grad = False

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(
        filter(lambda p: p.requires_grad, model.parameters()), lr=args.lr
    )
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.5)

    best_val_acc = 0.0

    for epoch in range(args.epochs):
        # Unfreeze after epoch 3
        if epoch == 3:
            for param in model.features.parameters():
                param.requires_grad = True
            optimizer = torch.optim.Adam(model.parameters(), lr=args.lr * 0.1)
            print("  → Unfroze feature extractor (fine-tuning all layers)")

        # Train
        model.train()
        train_loss, train_correct, train_total = 0.0, 0, 0
        for imgs, labels in train_loader:
            imgs, labels = imgs.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(imgs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * imgs.size(0)
            _, predicted = outputs.max(1)
            train_correct += predicted.eq(labels).sum().item()
            train_total += imgs.size(0)

        # Validate
        model.eval()
        val_correct, val_total = 0, 0
        with torch.no_grad():
            for imgs, labels in val_loader:
                imgs, labels = imgs.to(device), labels.to(device)
                outputs = model(imgs)
                _, predicted = outputs.max(1)
                val_correct += predicted.eq(labels).sum().item()
                val_total += imgs.size(0)

        train_acc = 100.0 * train_correct / train_total
        val_acc = 100.0 * val_correct / val_total
        avg_loss = train_loss / train_total
        scheduler.step()

        print(
            f"Epoch {epoch+1:2d}/{args.epochs} | "
            f"Loss: {avg_loss:.4f} | "
            f"Train Acc: {train_acc:.1f}% | "
            f"Val Acc: {val_acc:.1f}%"
        )

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            torch.save(model.state_dict(), output_path)
            print(f"  → Saved best model (val_acc={val_acc:.1f}%)")

    print(f"\n✅ Training complete. Best val accuracy: {best_val_acc:.1f}%")
    print(f"   Model saved to {args.output}")


if __name__ == "__main__":
    main()
