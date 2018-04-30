from bigchaindb_driver.exceptions import BadRequest

from chatbots.backends.bdb.utils import (
    prepare_transfer_ed25519_simple,
    sign_ed25519,
)


def get(query, connection):
    query = "\"{}\"".format(query)

    print('bdb::get::{}'.format(query))
    assets = connection.assets.get(search=query)
    print('bdb::result::len {}'.format(len(assets)))
    return assets


def history(asset_id, connection):
    return [
        {
            'data': transaction['metadata'],
            'id': transaction['id'],
            'tx': transaction
        }
        for transaction in connection.transactions.get(asset_id=asset_id)
    ]


def put(asset, metadata, connection, key_pair, unspent=None):

    if unspent:
        transfer_tx = prepare_transfer_ed25519_simple(
            transaction=unspent,
            receiver=key_pair.public_key,
            metadata=metadata
        )

        signed_tx = sign_ed25519(transfer_tx, key_pair.private_key)
    else:
        prepared_creation_tx = connection.transactions.prepare(
            operation='CREATE',
            signers=key_pair.public_key,
            asset={
                'data': asset
            },
            metadata=metadata
        )

        signed_tx = connection.transactions.fulfill(
            prepared_creation_tx,
            private_keys=key_pair.private_key
        )
    if signed_tx:
        try:
            sent_tx = connection.transactions.send(signed_tx)
        except BadRequest as e:
            print(e)
        print('bdb::put::{}'.format(sent_tx['id']))
        return signed_tx
    return None
