import React from "react";
import {addTrackToPlaylist, Track} from "./api";
import {createStyles, Theme, WithStyles, withStyles} from "@material-ui/core/styles";
import IconButton from '@material-ui/core/IconButton';

import Add from '@material-ui/icons/PlaylistAddRounded';
import AddCheck from '@material-ui/icons/PlaylistAddCheckRounded';
import {PlaylistContext} from "./Playlist";


const styles = (theme: Theme) => createStyles({
    icon: {
        backgroundColor: 'white',
        borderRadius: '10%',
    }
});

interface Props extends WithStyles<typeof styles> {
    track: Track;
    withBackground: boolean;
}

class AddToPlaylistButton extends React.Component<Props, {}> {

    public static defaultProps = {
        withBackground: false
    };

    render() {
        const {classes} = this.props;
        let iconClasses = '';
        if (this.props.withBackground) {
            iconClasses = classes.icon;
        }
        return (
            <PlaylistContext.Consumer>
                {playlistContext => (
                    <IconButton color="primary" onClick={() => addTrackToPlaylist(this.props.track.url)}
                                disabled={this.props.track.track_type === 'null'}>
                        {playlistContext.playlistTrackUrls.has(this.props.track.url) ?
                            <AddCheck fontSize="small" className={iconClasses}/> : <Add fontSize="small" className={iconClasses}/>}
                    </IconButton>
                )}
            </PlaylistContext.Consumer>
        )
    }
}

export default withStyles(styles)(AddToPlaylistButton);
