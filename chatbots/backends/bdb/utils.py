from time import sleep
# Separate all crypto code so that we can easily test several implementations
from collections import namedtuple

import nacl.signing
import sha3
from cryptoconditions import crypto

import bigchaindb_driver.exceptions


def poll_status_and_fetch_transaction(txid, connection):
    trials = 0
    tx_retrieved = None
    while trials < 100:
        try:
            res = connection.transactions.status(txid)
            print("Fetched transaction status: {}".format(res))
            if res.get('status') == 'valid':
                tx_retrieved = connection.transactions.retrieve(txid)
                print("Fetched transaction", tx_retrieved)
                break
        except bigchaindb_driver.exceptions.NotFoundError:
            trials += 1
        sleep(0.5)
    return tx_retrieved


def prepare_transfer(inputs, outputs, metadata=None):
    """Create an instance of a :class:`~.Output`.

    Args:
        inputs (list of
                    (dict):
                        {
                            'tx': <(bigchaindb.common.transactionTransaction):
                                    input transaction, can differ but must have same asset id>,
                            'output': <(int): output index of tx>
                        }
                )
        outputs (list of
                    (dict):
                        {
                            'condition': <(cryptoconditions.Condition): output condition>,
                            'public_keys': <(optional list of base58): for indexing defaults to `None`>,
                            'amount': <(int): defaults to `1`>
                        }
                )
        metadata (dict)
    Raises:
        TypeError: if `public_keys` is not instance of `list`.
            """
    from bigchaindb.common.transaction import (
        Input,
        Output,
        Transaction,
        TransactionLink
    )
    from cryptoconditions import (
        Fulfillment,
        Condition
    )

    asset = inputs[0]['tx']['asset']
    asset = {
        'id': asset['id'] if 'id' in asset else inputs[0]['tx']['id']
    }

    _inputs, _outputs = [], []

    for _input in inputs:

        _output = _input['tx']['outputs'][_input['output']]
        _inputs.append(
            Input(
                fulfillment=Condition.from_uri(_output['condition']['uri']),
                owners_before=_output['public_keys'],
                fulfills=TransactionLink(
                    txid=_input['tx']['id'],
                    output=_input['output'])
            )
        )

    for output in outputs:
        _outputs.append(
            Output(
                fulfillment=output['condition'],
                public_keys=output['public_keys'] if "public_keys" in output else None,
                amount=output['amount'] if "amount" in output else 1
            )
        )

    return Transaction(
        operation='TRANSFER',
        asset=asset,
        inputs=_inputs,
        outputs=_outputs,
        metadata=metadata,
    )


def prepare_transfer_ed25519_simple(transaction, receiver, metadata=None):
    from cryptoconditions import Ed25519Sha256
    from cryptoconditions.crypto import Ed25519VerifyingKey

    return prepare_transfer(
        inputs=[
            {
                'tx': transaction,
                'output': 0
            }
        ],
        outputs=[
            {
                'condition': Ed25519Sha256(public_key=Ed25519VerifyingKey(receiver).encode('bytes')),
                'public_keys': [receiver],
                'amount': 1
            }
        ],
        metadata=metadata)


def sign_ed25519(transaction, private_keys):
    from cryptoconditions import Ed25519Sha256
    from cryptoconditions.crypto import Ed25519VerifyingKey

    for index, _input in enumerate(transaction.inputs):
        receiver = _input.owners_before[0]
        transaction.inputs[index].fulfillment = Ed25519Sha256(
            public_key=Ed25519VerifyingKey(receiver).encode('bytes')
        )

    private_keys = [private_keys] if not isinstance(private_keys, list) else private_keys
    return transaction.sign(private_keys).to_dict()


def get_message_to_sign(transaction):
    from bigchaindb.common.transaction import Transaction
    # fulfillments are not part of the message to sign
    tx_dict = Transaction._remove_signatures(transaction.to_dict())
    return Transaction._to_str(tx_dict).encode()


CryptoKeypair = namedtuple('CryptoKeypair', ('private_key', 'public_key'))


def hash_data(data):
    """Hash the provided data using SHA3-256"""
    return sha3.sha3_256(data.encode()).hexdigest()


class Ed25519SigningKeyFromHash(crypto.Ed25519SigningKey):

    def __init__(self, key, encoding='base58'):
        super().__init__(key, encoding=encoding)

    @classmethod
    def generate(cls, hash_bytes):
        return cls(nacl.signing.SigningKey(hash_bytes).encode(encoder=crypto.Base58Encoder))


def ed25519_generate_key_pair_from_secret(secret):
    """
    Generate a new key pair.

    Args:
        secret (:class:`string`): A secret that serves as a seed

    Returns:
        A tuple of (private_key, public_key) encoded in base58.
    """

    # if you want to do this correctly, use a key derivation function!
    if not isinstance(secret, bytes):
        secret = secret.encode()

    hash_bytes = sha3.keccak_256(secret).digest()
    sk = Ed25519SigningKeyFromHash.generate(hash_bytes=hash_bytes)
    # Private key
    private_value_base58 = sk.encode(encoding='base58')

    # Public key
    public_value_compressed_base58 = sk.get_verifying_key().encode(encoding='base58')

    return private_value_base58, public_value_compressed_base58


def generate_key_pair(secret=None):
    """Generates a cryptographic key pair.
    Args:
        secret (:class:`string`): A secret that serves as a seed

    Returns:
        :class:`~bigchaindb.common.crypto.CryptoKeypair`: A
        :obj:`collections.namedtuple` with named fields
        :attr:`~bigchaindb.common.crypto.CryptoKeypair.private_key` and
        :attr:`~bigchaindb.common.crypto.CryptoKeypair.public_key`.

    """
    if secret:
        keypair_raw = ed25519_generate_key_pair_from_secret(secret)
    else:
        keypair_raw = crypto.ed25519_generate_key_pair()
    # TODO FOR CC: Adjust interface so that this function becomes unnecessary
    return CryptoKeypair(
        *(k.decode() for k in keypair_raw))

