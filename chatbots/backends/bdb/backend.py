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
    return connection.transactions.get(asset_id=asset_id)


def put(asset, metadata, connection, key_pair, unspent=None):

    if unspent:
        transfer_asset = {'id': unspent['id'] if unspent['operation'] == "CREATE" else unspent['asset']['id']}
        output_index = 0
        output = unspent['outputs'][output_index]
        transfer_input = {'fulfillment': output['condition']['details'],
                          'fulfills': {'output_index': output_index,
                                       'transaction_id': unspent['id']},
                          'owners_before': output['public_keys']}

        # prepare the transaction and use 3 tokens
        prepared_transfer_tx = connection.transactions.prepare(
            operation='TRANSFER',
            asset=transfer_asset,
            metadata=metadata,
            inputs=transfer_input,
            recipients=[([key_pair.public_key], 1)])

        # fulfill and send the transaction
        signed_tx = connection.transactions.fulfill(
            prepared_transfer_tx,
            private_keys=key_pair.private_key)
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
            sent_tx = connection.transactions.send_commit(signed_tx)
            print('bdb::put::{}'.format(sent_tx['id']))
        except BadRequest as e:
            print(e)
        return signed_tx
    return None
