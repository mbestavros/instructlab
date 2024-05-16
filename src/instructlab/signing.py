# SPDX-License-Identifier: Apache-2.0

# Standard
from pathlib import Path
import hashlib

# Third Party
from sigstore.hashes import Hashed
from sigstore.models import Bundle
from sigstore.oidc import Issuer
from sigstore.sign import SigningContext
from sigstore.verify import Verifier
from sigstore.verify.policy import Identity
from sigstore_protobuf_specs.dev.sigstore.common.v1 import HashAlgorithm


def sign_model(model_path: Path, bundle_path: Path, staging: bool = False) -> None:
    """Signs a model with Sigstore"""

    # Sigstore setup
    if staging:
        issuer = Issuer.staging()
        signing_ctx = SigningContext.staging()
    else:
        issuer = Issuer.production()
        signing_ctx = SigningContext.production()
    identity = issuer.identity_token()

    # Hash the model file
    model_hash = incremental_hash(model_path=model_path)

    # Sign the model's hash and write Sigstore bundle to disk
    with signing_ctx.signer(identity, cache=True) as signer:
        result = signer.sign_artifact(model_hash)
    with bundle_path.open("w", encoding="utf8") as bundle_file:
        bundle_file.write(result.to_json())


def verify_model(
    model_path: Path,
    bundle_path: Path,
    identity: str,
    issuer: str,
    staging: bool = False,
) -> None:
    """Verifies a model and its bundle with Sigstore"""

    # Sigstore setup
    if staging:
        verifier = Verifier.staging()
    else:
        verifier = Verifier.production()

    # Hash the model file
    model_hash = incremental_hash(model_path=model_path)

    # Read the Sigstore bundle to verify with from disk
    bundle = Bundle.from_json(bundle_path.read_bytes())

    # Verify the model hash against the bundle
    verifier.verify_artifact(
        model_hash,
        bundle,
        Identity(
            identity=identity,
            issuer=issuer,
        ),
    )


def incremental_hash(model_path: Path) -> Hashed:
    """Incrementally hash a file and create a sigstore.hashes.Hashed object"""
    h = hashlib.sha256()
    with model_path.open("rb") as f:
        while True:
            buf = f.read(128 * 1024)
            if not buf:
                break
            h.update(buf)
    return Hashed(algorithm=HashAlgorithm.SHA2_256, digest=h.digest())
