import React from "react";
import {addTrackToPlaylist, Track} from "./api";
import {createStyles, Theme, WithStyles, withStyles} from "@material-ui/core/styles";
import IconButton from '@material-ui/core/IconButton';

import Add from '@material-ui/icons/PlaylistAddRounded';
import AddCheck from '@material-ui/icons/PlaylistAddCheckRounded';
import {PlaylistContext} from "./Playlist";


const styles = (theme: Theme) => createStyles({});

interface Props extends WithStyles<typeof styles> {
    track: Track;
}

class AddToPlaylistButton extends React.Component<Props, {}> {

    render() {
        return (
            <PlaylistContext.Consumer>
                {playlistContext => (
                    <IconButton color="primary" onClick={() => addTrackToPlaylist(this.props.track.url)}
                                disabled={this.props.track.track_type === 'null'}>
                        {playlistContext.playlistTrackUrls.has(this.props.track.url) ?
                            <AddCheck fontSize="small"/> : <Add fontSize="small"/>}
                    </IconButton>
                )}
            </PlaylistContext.Consumer>
        )
    }
}

export default withStyles(styles)(AddToPlaylistButton);
