import React from "react";
import {currentTrack, NULL_TRACK, Track} from "./api";

import {createStyles, Theme, WithStyles, withStyles} from "@material-ui/core/styles";
import Typography from '@material-ui/core/Typography';
import PlayPauseControl from "./PlayPauseControl";
import Grid from '@material-ui/core/Grid';
import TrackProgressControl from "./TrackProgressControl";
import AddToPlaylistButton from "./AddToPlaylistButton";
import {PlaylistContext} from "./Playlist";
import { Paper } from "@material-ui/core";

var Textfit = require('react-textfit').default;


interface State {
    currentTrack: Track;
}

const styles = (theme: Theme) => createStyles({
    paper: {
        margin: '5px',
        minHeight: '142px',
        flex: 1.5,
        display: 'flex',
        overflow: 'hidden',
    },
    outerGridContainer: {
        width: '100%',
        display: 'flex',
        flexDirection: 'row',
    },
    coverImageGridItem: {
        backgroundColor: 'black',
        backgroundSize: 'contain',
        backgroundRepeat: 'no-repeat',
        backgroundPosition: 'center',
    },
    controlPanelGridItem: {
        paddingLeft: '5px',
    },
    controlPanelGridContainer: {
        padding: '5px',
        height: '100%',
    },
    titleText: {
        height: '25px',
        lineHeight: '1'
    },
    artistText: {
        height: '16px',
        lineHeight: '1'
    },
    metaButtonContainer: {
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'flex-start',
        alignItems: 'flex-start',
        height: '100%'
    }
});

interface Props extends WithStyles<typeof styles> {}

class CurrentTrackPanel extends React.Component<Props, State> {

    constructor(props: Props) {
        super(props);
        this.state = CurrentTrackPanel.getNullTrack();
        this.setCurrentTrack = this.setCurrentTrack.bind(this);
    }

    componentDidMount() {
        currentTrack(this.setCurrentTrack)
    }

    setCurrentTrack(track: Track): void {
        if (track.track_type === 'null') {
            this.setState(CurrentTrackPanel.getNullTrack());
        } else {
            this.setState({currentTrack: track});
        }
    }

    static getNullTrack(): State {
        return {currentTrack: NULL_TRACK};
    }

    render() {
        const { classes } = this.props;
        return (
            <Paper className={classes.paper}>
                <Grid container className={classes.outerGridContainer}>
                    <Grid item xs={4} className={classes.coverImageGridItem} style={{ backgroundImage: `url(${this.state.currentTrack.cover_url})` }} >
                        <div className={classes.metaButtonContainer}>
                            <AddToPlaylistButton track={this.state.currentTrack} withBackground={true}/>
                        </div>
                    </Grid>
                    <Grid item xs={8} className={classes.controlPanelGridItem}>
                        <Grid container className={classes.controlPanelGridContainer}>
                            <Grid item xs={12} >
                                <Typography component="h6" variant="h6" align={"left"} className={classes.titleText}>
                                    <Textfit mode="single" max={25} >
                                    {this.state.currentTrack.title}
                                    </Textfit>
                                </Typography>
                            </Grid>
                            <Grid item xs={12} >
                                <Typography variant="subtitle1" color="textSecondary" align={"left"} className={classes.artistText}>
                                    <Textfit mode="single" max={16} >
                                        {this.state.currentTrack.artist}
                                    </Textfit>
                                </Typography>
                            </Grid>
                            <Grid item xs={12}>
                                <PlaylistContext.Consumer>
                                    {playlistContext => (
                                        <PlayPauseControl playlistItems={playlistContext.playlistItems}/>
                                    )}
                                </PlaylistContext.Consumer>
                            </Grid>
                            <Grid item xs={12}>
                                <TrackProgressControl track={this.state.currentTrack}/>
                            </Grid>
                        </Grid>
                    </Grid>
                </Grid>
            </Paper>
        );
    }
}
export default withStyles(styles) (CurrentTrackPanel);
