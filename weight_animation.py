import matplotlib

matplotlib.use("PDF")
from matplotlib import pyplot as plt
from matplotlib import animation, rc
import numpy as np
import pandas as pd
from scipy import sparse

from utilities import plot_weights, rearrange_weights, rreplace

rc("animation", html="html5")


def weight_animation(store_filename, conn, gif_filename="weights_example", sample=None):
    with pd.HDFStore(store_filename, "r") as store:
        nseen = store.select("nseen")
        if sample is not None:
            nseen = nseen.iloc[::sample]
        firstseen = nseen.iloc[0]
        weights0 = store.select(
            f"connections/{conn}", where="nseen == firstseen"
        ).reset_index("nseen", drop=True)
        weights0 = sparse.coo_matrix((weights0.w, (weights0.i, weights0.j))).todense()
        assignments0 = store.select(
            f"assignments/{conn[-2:]}", where="nseen == firstseen"
        ).reset_index("nseen", drop=True)
        theta0 = store.select(f"theta/{conn[-2:]}", where="nseen == firstseen")
        fig, ax, img, assignments_text, theta_text = plot_weights(
            weights0,
            assignments=assignments0,
            theta=theta0,
            max_weight=1.0,
            return_artists=True,
        )
        title = ax.set_title("", loc="right")
        n = len(theta0)

        def init():
            update_image(nseen[0])
            return [title, img]

        def animate(t):
            update_image(t)
            return [title, img]

        def update_image(t):
            weights = store.select(
                f"connections/{conn}", where="nseen == t"
            ).reset_index("nseen", drop=True)
            weights = sparse.coo_matrix((weights.w, (weights.i, weights.j))).todense()
            rearranged_weights = rearrange_weights(weights)
            arr = img.get_array()
            arr[:] = rearranged_weights
            title.set_text(f"examples seen: {t}")
            assignments = store.select(
                f"assignments/{conn[-2:]}", where="nseen == t"
            ).reset_index("nseen", drop=True)
            ass = np.zeros(n, np.int) - 1
            ass[assignments.index] = assignments["label"]
            ass = ass.astype(np.str)
            ass[ass == "-1"] = ""
            theta = store.select(f"theta/{conn[-2:]}", where="nseen == t")
            theta = theta.values * 1000  # mV
            for k in range(n):
                assignments_text[k].set_text(ass[k])
                theta_text[k].set_text(f"{theta[k]:4.2f}")

        duration = 10000  # ms
        anim = animation.FuncAnimation(
            fig,
            animate,
            init_func=init,
            frames=nseen,
            interval=duration / len(nseen),
            repeat=False,
            blit=True,
        )
        plt.close()
        if gif_filename is not None:
            anim.save(
                "{}.gif".format(rreplace(gif_filename, ".gif", "")),
                writer="imagemagick",
                fps=1000 * len(nseen) / duration,
            )
    return anim


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description=("Create weights animation from output store.")
    )

    parser.add_argument("store_filename", type=str, help="Filename of HDF5 store")
    parser.add_argument("conn", type=str, help="Connection name")
    parser.add_argument(
        "--gif_filename",
        type=str,
        default="weights_example",
        help="Filename of output gif",
    )
    parser.add_argument("--sample", type=int, help="Sampling factor")

    args = parser.parse_args()

    sys.exit(
        weight_animation(
            store_filename=args.store_filename,
            conn=args.conn,
            gif_filename=args.gif_filename,
            sample=args.sample,
        )
    )
