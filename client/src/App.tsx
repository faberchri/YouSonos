import React, {Component} from 'react';
import DeviceControl from './DeviceControl'
import {createStyles, Theme, WithStyles, withStyles} from '@material-ui/core/styles';
import SearchAndManageTracks from "./SearchAndManageTracks";
import CurrentTrackCoverPanel from "./CurrentTrackPanel";
import {initSocket} from "./api";
import {PlaylistContextProvider} from "./Playlist";

const styles = (theme: Theme) => createStyles({

    app: {
        textAlign: 'center',
        display: 'flex',
        flexFlow: 'column',
        height: '100%',
    },
    paper: {
        margin: '5px',
    }
});

interface Props extends WithStyles<typeof styles> {}

class App extends Component<Props, {}> {

    constructor(props: Props) {
        super(props);
        initSocket();
    }

    render() {
        const { classes } = this.props;

        return (
            <div className={classes.app}>
                <PlaylistContextProvider>
                    <CurrentTrackCoverPanel />
                    <DeviceControl/>
                    <SearchAndManageTracks/>
                </PlaylistContextProvider>
            </div>

        );
    }
}

export default withStyles(styles) (App);
